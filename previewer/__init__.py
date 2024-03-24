import signal
import multiprocessing as mp
if mp.current_process().name == 'ipython_previewer':
    # on windows, ctrl+c propegate to terminal's subprocess, and there is good chance
    # user would ctrl+c while previewer is restarting, mask it as long there is no handling
    signal.signal(signal.SIGINT, signal.SIG_IGN)

import threading
import os
import io
import ast
import sys
from types import ModuleType
import traceback
import IPython
from prompt_toolkit.styles import Style, merge_styles
from traitlets.config.loader import Config

CTRL_C_TIMEOUT = 2
RESTART_TIMEOUT = 10
NS_BLOCK_LIST = ['open', 'exit', 'quit', 'get_ipython', 'calcpy']

class PipeListener(threading.Thread):
    def __init__(self, conn, cb):
        super().__init__(name=cb.__name__, daemon=True)
        self.conn = conn
        self.cb = cb
        self.start()

    def run(self):
        while True:
            try:
                msg = self.conn.recv()
            except (EOFError, OSError):
                return # pipe closed
            self.cb(msg)

class DisableAssignments(ast.NodeTransformer):
    def __init__(self, active):
        super().__init__()
        self.active = active

    def visit_Assign(self, node):
        if self.active:
            return ast.Expr(node.value)
        return self.generic_visit(node)

    def visit_AugAssign(self, node):
        if self.active:
            node.target.ctx = ast.Load()
            return ast.Expr(ast.BinOp(left=node.target, op=node.op, right=node.value))
        return self.generic_visit(node)

    def visit_Delete(self, node):
        if self.active:
            return ast.Expr(ast.Constant(None))
        return self.generic_visit(node)

class IPythonProcess(mp.Process):
    def __init__(self, exec_conn, ctrl_conn, ns_conn, config=Config(), formatter=str, debug=False, stdout_path=None, interactive=False):
        super().__init__(name='ipython_previewer', daemon=True)
        self.exec_conn = exec_conn
        self.ctrl_conn = ctrl_conn
        self.ns_conn = ns_conn
        self.config = config
        self.formatter = formatter
        self.debug = debug
        self.stdout_path = stdout_path
        self.interactive = interactive
        self._open = io.open
        self.start()

    def sandbox_pre(self):
        for module_name in ['matplotlib', 'tkinter', 'pyperclip']:
            sys.modules[module_name] = None

    def previewer_open(self, file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        if any(['importlib' in fs.filename for fs in traceback.extract_stack()]) or \
           file == os.devnull:
            return self._open(file, mode=mode, buffering=buffering, encoding=encoding, errors=errors, newline=newline, closefd=closefd, opener=opener)
        else:
            raise IOError('open is not allowed in previewer')

    def sandbox_post(self):
        try:
            # cache tz before removing access to it
            import tzlocal
            tzlocal.reload_localzone()
        except: # reload_localzone crashes on termux ModuleNotFoundError+ZoneInfoNotFoundError
            pass
        try:
            # numpy util function need access to subprocess.run
            from numpy.testing._private.utils import _SUPPORTS_SVE
        except (ModuleNotFoundError, ImportError):
            pass
        import subprocess
        subprocess.Popen = None
        import builtins
        builtins.open = self.previewer_open
        io.open = self.previewer_open
        os.exit = None
        os.abort = None
        os.kill = None
        os.system = None
        for key in NS_BLOCK_LIST:
            self.previewer_ip.user_ns.pop(key, None)

    def initialize(self):
        self.sandbox_pre()
        # for execution to return result, but to not change _, __ etc.
        IPython.core.displayhook.DisplayHook.update_user_ns = lambda self, result: None
        self.config.TerminalInteractiveShell.simple_prompt = True
        self.config.TerminalInteractiveShell.term_title = False
        self.config.TerminalInteractiveShell.xmode = 'Minimal'
        self.config.HistoryAccessor.enabled = False
        self.ipapp = IPython.terminal.ipapp.TerminalIPythonApp.instance(config=self.config)
        self.ipapp.initialize()
        self.previewer_ip = self.ipapp.shell
        self.previewer_ip.inspector = None # inspector is calling expensive operations
        self.disable_assign = DisableAssignments(False)
        self.previewer_ip.ast_transformers.append(self.disable_assign)
        self.ns_thread = threading.Thread(target=self.ns_job, daemon=True, name='ns_job')
        self.ns_thread.start()

        self.sandbox_post()

    def ns_job(self):
        while True:
            try:
                ns_msg = self.ns_conn.recv()
                if ns_msg[0] in NS_BLOCK_LIST:
                    continue
                if len(ns_msg) == 2:
                    self.previewer_ip.user_ns[ns_msg[0]] = ns_msg[1]
                elif len(ns_msg) == 3:
                    self.previewer_ip.user_ns[ns_msg[0]][ns_msg[1]] = ns_msg[2]
            except (EOFError, OSError):
                return # pipe closed
            except Exception as e:
                print(f'ns error: {repr(e)}')

    def ask_restart(self):
        print('asking restart')
        self.ctrl_conn.send('restart')

    def ctrl_c(self):
        print('sending SIGINT')
        signal.raise_signal(signal.SIGINT)

    def run(self):
        if self.interactive:
            sys.stdin = open(0)
            self.stdout = sys.stdout
        else:
            sys.stdin = None
            if self.debug and self.stdout_path:
                self.stdout = open(self.stdout_path, 'a')
            else:
                self.stdout = open(os.devnull, 'w')
        sys.stderr = sys.stdout = self.stdout

        print('previewer initialize')
        self.initialize()

        if self.interactive:
            self.ipapp.start()
            return

        while True:
            try:
                code, assign, do_preview = self.exec_conn.recv()
                while self.exec_conn.poll(): # take only latest
                    code, assign, do_preview = self.exec_conn.recv()
                # unmask ctrl+c
                signal.signal(signal.SIGINT, signal.default_int_handler)
                ctrl_c_timer = threading.Timer(CTRL_C_TIMEOUT, self.ctrl_c)
                restart_timer = threading.Timer(RESTART_TIMEOUT, self.ask_restart)
                ctrl_c_timer.start(),  restart_timer.start()
                result = self.run_code(code, assign)
                ctrl_c_timer.cancel(), restart_timer.cancel()
                if do_preview:
                    self.exec_conn.send(result)
            except (EOFError, OSError):
                return # pipe closed
            except Exception as e:
                print(f'previewer run cell error: {repr(e)}')
            finally:
                signal.signal(signal.SIGINT, signal.SIG_IGN)

    def run_code(self, code, assign):
        self.disable_assign.active = not assign
        print(f'In [1]: {code}')
        result = self.previewer_ip.run_cell(code, store_history=False)
        if result.result is None:
            return ''
        return self.formatter(result.result)

class Previewer():
    def __init__(self, ip, config=Config(), formatter=str, debug=False):
        # spawn, so no memory leftovers (e.g. traitlets singletons)
        mp.set_start_method('spawn', force=True)
        self.ip = ip
        self.config = ip.config.copy()
        self.config.merge(config)
        self.formatter = formatter
        self.debug = debug

        if debug:
            debug_path = os.path.join(ip.profile_dir.location, 'debug')
            os.makedirs(debug_path, exist_ok=True)
            self.stdout_path = os.path.join(debug_path, 'previewer_stdout.txt')
        else:
            self.stdout_path = None
        self.ip.pt_app.style = merge_styles([self.ip.pt_app.style,
            Style([('bottom-toolbar', 'noreverse')])])
        self.start()

    def start(self):
        self.exec_conn, exec_conn_c = mp.Pipe()
        self.ctrl_conn, ctrl_conn_c = mp.Pipe()
        self.ns_conn, ns_conn_c = mp.Pipe()
        self.preview_thread = PipeListener(self.exec_conn, self.preview_cb)
        self.ctrl_thread = PipeListener(self.ctrl_conn, self.ctrl_cb)
        self.prev_ip_proc = IPythonProcess(exec_conn_c, ctrl_conn_c, ns_conn_c,
            config=self.config, formatter=self.formatter, debug=self.debug, stdout_path=self.stdout_path)
        self.push(self.ip.user_ns)
        self.ip.events.register('pre_run_cell', self.pre_run_cell)
        self.ip.events.register('post_run_cell', self.post_run_cell)
        self.ip.pt_app.default_buffer.on_text_changed.add_handler(self.text_changed_handler)
        self.ip.pt_app.bottom_toolbar = ''

    def deinit(self):
        self.ip.events.unregister('pre_run_cell', self.pre_run_cell)
        self.ip.events.unregister('post_run_cell', self.post_run_cell)
        self.ip.pt_app.default_buffer.on_text_changed.remove_handler(self.text_changed_handler)
        self.exec_conn.close()
        self.ctrl_conn.close()
        self.ns_conn.close()
        self.prev_ip_proc.terminate()

    def restart(self):
        self.deinit()
        self.start()

    def run_cell(self, raw_cell, assign=True, preview=False):
        self.exec_conn.send((raw_cell, assign, preview))

    def pre_run_cell(self, info):
        # run the code with assignments to align the namespace (no preview)
        self.run_cell(info.raw_cell, assign=True, preview=False)

    def post_run_cell(self, result):
        self.push(self.ip.user_ns)
        Out = self.ip.user_ns['Out']
        if len(Out) > 0:
            Out_last = list(Out)[-1]
            self.push_kv('Out', Out_last, Out[Out_last])
        self.ip.pt_app.bottom_toolbar = ''
        self.ip.pt_app.app.invalidate()

    def ctrl_cb(self, ctrl_msg):
        if ctrl_msg == 'restart':
            self.restart()

    def preview_cb(self, result):
        self.ip.pt_app.bottom_toolbar = result
        self.ip.pt_app.app.invalidate()

    def text_changed_handler(self, buffer):
        self.run_cell(buffer.text, assign=False, preview=True)

    def push(self, variables):
        for var_name, val in variables.copy().items():
            if var_name in NS_BLOCK_LIST or isinstance(val, ModuleType):
                continue
            try:
                self.ns_conn.send((var_name, val))
            except Exception as e:
                if self.debug and var_name != 'Out':
                    self.ns_conn.send((var_name, repr(e)))

    def push_kv(self, var_name, key, value):
        try:
            self.ns_conn.send((var_name, key, value))
        except Exception as e:
            if self.debug:
                self.ns_conn.send((var_name, key, repr(e)))

    def get_stdout(self):
        if self.stdout_path == None:
            raise NotImplementedError('Previewer stdout available only when debug=True')
        with open(self.stdout_path, 'r') as f:
            return f.read()

def load_ipython_extension(ip:IPython.InteractiveShell, config=None, formatter=str, debug=False):
    if config is None:
        config = ip.config.copy()
    if getattr(ip, 'pt_app', None) is None:
        return
    ip.previewer = Previewer(ip, config=config, formatter=formatter, debug=debug)

def unload_ipython_extension(ip:IPython.InteractiveShell):
    if getattr(ip, 'pt_app', None) is None:
        return
    ip.previewer.deinit()
    ip.pt_app.bottom_toolbar = None
    del ip.previewer
