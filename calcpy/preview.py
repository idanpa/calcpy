import multiprocessing as mp
import _thread
import inspect
import ast
import sys
import io
import IPython
from traitlets.config.loader import Config
from prompt_toolkit.buffer import _only_one_at_a_time, _Retry
from prompt_toolkit.eventloop import run_in_executor_with_context
from prompt_toolkit.application.current import get_app

from . import formatters

class DisableAssignments(ast.NodeTransformer):
    def visit_Assign(self, node):
        return ast.Expr(ast.Constant(None))
    def visit_AnnAssign(self, node):
        return ast.Expr(ast.Constant(None))
    def visit_AugAssign(self, node):
        return ast.Expr(ast.Constant(None))

class IPythonProcess(mp.Process):
    def __init__(self, config=Config(), formatter=str, debug=False):
        self.config = config
        self.formatter = formatter
        self.debug = debug
        self.exec_conn_p, self.exec_conn_c = mp.Pipe()
        self.ctrl_conn_p, self.ctrl_conn_c = mp.Pipe()
        self.ns_conn_p, self.ns_conn_c = mp.Pipe()
        super().__init__(name='ipython_preview', daemon=True)

    def execute(self, cell, timeout=6):
        # flush previous (possibly timeout) executions:
        while self.exec_conn_p.poll():
            self.exec_conn_p.recv()

        self.exec_conn_p.send(cell)
        if not self.exec_conn_p.poll(timeout):
            self.ctrl_conn_p.send('interrupt')
        if self.exec_conn_p.poll(0.5):
            return self.exec_conn_p.recv()
        else:
            raise TimeoutError

    def get_stdout(self):
        self.ctrl_conn_p.send('stdout')
        if self.ctrl_conn_p.poll(2):
            return self.ctrl_conn_p.recv()
        return ''

    def sandbox_pre(self):
        for module_name in ['matplotlib', 'tkinter', 'pyperclip']:
            sys.modules[module_name] = None

        sys.stdout = io.StringIO()
        if not self.debug:
            sys.stderr = sys.stdout
        sys.stdin = None

    def sandbox_post(self):
        import subprocess
        subprocess.Popen = None
        import builtins
        builtins.open = None
        import os
        os.exit = None
        os.abort = None
        os.kill = None
        os.system = None

    def exc_handler(self, ip:IPython.InteractiveShell, etype, value, tb, tb_offset=None):
        print(value)

    def format_res(self, obj):
        if obj is None:
            return ''
        return self.formatter(obj)

    def ctrl_job(self):
        while True:
            ctrl_msg = self.ctrl_conn_c.recv()
            if ctrl_msg == 'interrupt':
                _thread.interrupt_main()
            elif ctrl_msg == 'stdout':
                self.ctrl_conn_c.send(sys.stdout.getvalue())
            else:
                self.ctrl_conn_c.send('unexpected')

    def ns_job(self):
        while True:
            try:
                ns_msg = self.ns_conn_c.recv()
                self.ip.user_ns[ns_msg[0]] = ns_msg[1]
            except Exception as e:
                print(f'Previewer ns error: {repr(e)}', file=sys.stderr)

    def run(self):
        self.sandbox_pre()

        # for execution to return result, but to not change _, __ etc.
        IPython.core.displayhook.DisplayHook.update_user_ns = lambda self, result: None

        self.config.TerminalInteractiveShell.simple_prompt = True
        self.config.TerminalInteractiveShell.term_title = False
        self.ipapp = IPython.terminal.ipapp.TerminalIPythonApp.instance(config=self.config)
        self.ipapp.initialize()
        self.ip = self.ipapp.shell

        self.ip.previewer_jobs = IPython.lib.backgroundjobs.BackgroundJobManager()
        self.ip.previewer_jobs.new(self.ctrl_job, daemon=True)
        self.ip.previewer_jobs.new(self.ns_job, daemon=True)

        self.ip.ast_transformers.append(DisableAssignments())
        self.ip.set_custom_exc((Exception,), self.exc_handler)

        self.sandbox_post()

        while True:
            try:
                result = self.ip.run_cell(self.exec_conn_c.recv(), store_history=False).result
                self.exec_conn_c.send(self.format_res(result))
            except Exception as e:
                print(f'Previewer run cell error: {repr(e)}', file=sys.stderr)

class Previewer():
    def __init__(self, ip, timeout=6, config=Config(), formatter=str, debug=False):
        if getattr(ip, 'pt_app', None) is None:
            raise Exception('Preview: No prompt application')
        if mp.get_start_method() != 'spawn':
            mp.set_start_method('spawn')
        self.ip = ip
        self.timeout = timeout
        self.config = ip.config.copy()
        self.config.merge(config)
        self.prev_ip_proc = IPythonProcess(config=self.config, formatter=formatter, debug=debug)
        self.prev_ip_proc.start()
        self.update_ns()
        self.ip.pt_app.bottom_toolbar = ''
        self.ip.events.register('pre_run_cell', self.pre_run_cell)
        self.ip.events.register('post_run_cell', self.post_run_cell)
        self.ip.pt_app.default_buffer.on_text_changed.add_handler(self.text_changed_handler)

    def deinit(self):
        self.ip.events.unregister('pre_run_cell', self.pre_run_cell)
        self.ip.events.unregister('post_run_cell', self.post_run_cell)
        self.ip.pt_app.default_buffer.on_text_changed.remove_handler(self.text_changed_handler)
        self.ip.pt_app.bottom_toolbar = None
        self.prev_ip_proc.terminate()

    def push(self, variables):
        '''push dictionary of variables to previewer (skipping variables that cannot be sent)'''
        for key, val in variables.copy().items():
            if inspect.isbuiltin(val):
                continue
            if getattr(val, '__module__', None) == '__main__':
                continue
            try:
                self.prev_ip_proc.ns_conn_p.send((key, val))
            except Exception as e:
                pass

    def update_ns(self):
        self.push(self.ip.user_ns)

    def pre_run_cell(self, info):
        self.ip.pt_app.bottom_toolbar = ''
        get_app().invalidate()

    def post_run_cell(self, result):
        self.update_ns()

    def get_stdout(self):
        return self.prev_ip_proc.get_stdout()

    def preview(self, code):
        try:
            return self.prev_ip_proc.execute(code, self.timeout)
        except TimeoutError:
            return '' # TODO: restart process?

    @_only_one_at_a_time
    async def async_previewer(self, buffer):
        document = buffer.document
        preview = await run_in_executor_with_context(self.preview, buffer.text)
        if buffer.document == document:
            self.ip.pt_app.bottom_toolbar = preview
            get_app().invalidate()
        else: # text has changed, retry
            raise _Retry

    def text_changed_handler(self, buffer):
        get_app().create_background_task(self.async_previewer(buffer))

def load_ipython_extension(ip:IPython.InteractiveShell, timeout=6, config=Config(), formatter=str, debug=False):
    ip.previewer = Previewer(ip, timeout=timeout, config=config, formatter=formatter, debug=debug)

def unload_ipython_extension(ip:IPython.InteractiveShell):
    ip.previewer.deinit()
    del ip.previewer
