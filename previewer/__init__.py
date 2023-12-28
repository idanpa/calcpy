import signal
import multiprocessing as mp
if mp.current_process().name == 'ipython_previewer':
    # on windows, ctrl+c propegate to terminal's subprocess, and there is good chance
    # user would ctrl+c while previewer is restarting, mask it as long there is no handling
    signal.signal(signal.SIGINT, signal.SIG_IGN)

import threading
import _thread
import os
import ast
import sys
import IPython
from prompt_toolkit.styles import Style, merge_styles
from traitlets.config.loader import Config

CTRL_C_TIMEOUT = 2
RESTART_TIMEOUT = 10

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
        self.ns_block_list = ['open', 'exit', 'quit', 'get_ipython']
        self.start()

    def sandbox_pre(self):
        for module_name in ['matplotlib', 'tkinter', 'pyperclip']:
            sys.modules[module_name] = None

    def sandbox_post(self):
        try:
            # cache tz before removing access to it
            import tzlocal
            tzlocal.reload_localzone()
        except (ModuleNotFoundError, ImportError):
            pass
        import subprocess
        subprocess.Popen = None
        import builtins
        builtins.open = None
        import io
        io.open = None
        os.exit = None
        os.abort = None
        os.kill = None
        os.system = None
        for key in self.ns_block_list:
            self.ip.user_ns.pop(key, None)

    def ns_job(self):
        while True:
            try:
                ns_msg = self.ns_conn.recv()
                if ns_msg[0] in self.ns_block_list:
                    continue
                if len(ns_msg) == 2:
                    self.ip.user_ns[ns_msg[0]] = ns_msg[1]
                elif len(ns_msg) == 3:
                    self.ip.user_ns[ns_msg[0]][ns_msg[1]] = ns_msg[2]
            except (EOFError, OSError):
                return # pipe closed
            except Exception as e:
                print(f'ns error: {repr(e)}')

    def run(self):
        if self.interactive:
            sys.stdin = open(0)
        else:
            if self.debug and self.stdout_path:
                sys.stdout = open(self.stdout_path, 'a')
            else:
                sys.stderr = sys.stdout = open(os.devnull, 'w')
            sys.stdin = None

        self.sandbox_pre()
        # for execution to return result, but to not change _, __ etc.
        IPython.core.displayhook.DisplayHook.update_user_ns = lambda self, result: None
        self.config.TerminalInteractiveShell.simple_prompt = True
        self.config.TerminalInteractiveShell.term_title = False
        self.config.TerminalInteractiveShell.xmode = 'Minimal'
        self.config.HistoryAccessor.enabled = False
        self.ipapp = IPython.terminal.ipapp.TerminalIPythonApp.instance(config=self.config)
        self.ipapp.initialize()
        self.ip = self.ipapp.shell
        self.ip.inspector = None # inspector is calling expensive operations
        self.disable_assign = DisableAssignments(False)
        self.ip.ast_transformers.append(self.disable_assign)
        self.ns_thread = threading.Thread(target=self.ns_job, daemon=True, name='ns_job')
        self.ns_thread.start()

        self.sandbox_post()
        signal.signal(signal.SIGINT, signal.default_int_handler)

        if self.interactive:
            self.ipapp.start()
            return

        while True:
            try:
                code, assign, do_preview = self.exec_conn.recv()
                ctrl_c_timer = threading.Timer(CTRL_C_TIMEOUT, _thread.interrupt_main)
                restart_timer = threading.Timer(RESTART_TIMEOUT, self.ctrl_conn.send, ['restart'])
                ctrl_c_timer.start(),  restart_timer.start()
                result = self.run_code(code, assign)
                ctrl_c_timer.cancel(), restart_timer.cancel()
                if do_preview:
                    self.exec_conn.send(result)
            except (EOFError, OSError):
                return # pipe closed
            except Exception as e:
                print(f'previewer run cell error: {repr(e)}', file=sys.stderr)

    def run_code(self, code, assign):
        self.disable_assign.active = not assign
        print(f'In [1]: {code}')
        result = self.ip.run_cell(code, store_history=False)
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
        self.stdout_path = self.ip.mktempfile(prefix='previewer_stdout') if debug else None
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

    def pre_run_cell(self, info):
        self.exec_conn.send((info.raw_cell, True, False))

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
        self.exec_conn.send((buffer.text, False, True))

    def push(self, variables):
        for var_name, val in variables.copy().items():
            try:
                self.ns_conn.send((var_name, val))
            except Exception as e:
                pass

    def push_kv(self, var_name, key, value):
        try:
            self.ns_conn.send((var_name, key, val))
        except Exception as e:
            pass

    def get_stdout(self):
        if self.stdout_path == None:
            raise NotImplementedError('Previewer stdout available only when debug=True')
        with open(self.stdout_path, 'r') as f:
            return f.read()

def load_ipython_extension(ip:IPython.InteractiveShell, config=Config(), formatter=str, debug=False):
    if ip.config.TerminalInteractiveShell.simple_prompt == True:
        return
    ip.previewer = Previewer(ip, config=config, formatter=formatter, debug=debug)

def unload_ipython_extension(ip:IPython.InteractiveShell):
    if ip.config.TerminalInteractiveShell.simple_prompt == True:
        return
    ip.previewer.deinit()
    ip.pt_app.bottom_toolbar = None
    del ip.previewer
