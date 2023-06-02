import sympy
import IPython
from prompt_toolkit.buffer import _only_one_at_a_time, _Retry
from prompt_toolkit.eventloop import run_in_executor_with_context
from prompt_toolkit.application.current import get_app
from contextlib import redirect_stdout
from types import ModuleType
from copy import deepcopy
import shutil
import ast

from . import transformers

class Previewer():
    def __init__(self, ip):
        self.ip = ip
        self.update_isolated_ns()

    def update_isolated_ns(self):
        self.isolated_ns = {}
        for key in list(self.ip.user_ns):
            if isinstance(self.ip.user_ns[key], ModuleType):
                self.isolated_ns[key] = self.ip.user_ns[key]
                continue
            try:
                # TODO: this does not solves the case of def test1(): global t; t=3
                self.isolated_ns[key] = deepcopy(self.ip.user_ns[key])
            except:
                pass

    def pre_run_cell(self, info):
        self.ip.pt_app.bottom_toolbar = None
        get_app().invalidate()
        # TODO: get_app().invalidate()/_redraw() are not cleaning bottom_toolbar (not fast enough?)

    def post_run_cell(self, result):
        self.update_isolated_ns()

    def preview(self, code):
        PyCF_DONT_IMPLY_DEDENT = 0x200
        code = transformers.calcpy_input_transformer_post([code])[0]

        try:
            ast_code = compile(code, '<string>', 'eval', ast.PyCF_ONLY_AST | PyCF_DONT_IMPLY_DEDENT, 1)
        except:
            return None
        ast_code = self.ip.transform_ast(ast_code)

        with redirect_stdout(None):
            try:
                compiled_code = compile(ast_code, '<string>', 'eval', PyCF_DONT_IMPLY_DEDENT, 1)
                result = eval(compiled_code, self.isolated_ns)
            except:
                return None

        if isinstance(result, (int, sympy.Integer, sympy.Float)):
            result_str = str(result)
        elif isinstance(result, sympy.Expr):
            result_str = sympy.printing.pretty(sympy.N(result))
        else:
            result_str = self.ip.display_formatter.format(result)[0]['text/plain']

        if '\n' in result_str or len(result_str) > shutil.get_terminal_size().columns:
            return None

        return result_str

    async def preview_async(self, code):
        def run_get_preview_thread():
            return self.preview(code)
        return await run_in_executor_with_context(run_get_preview_thread)

def create_preview_coroutine(ip, buffer, previewer):
    # TODO: retry might not be enough, need to timeout or cancel upon new event
    @_only_one_at_a_time
    async def async_previewer():
        document = buffer.document
        preview = await previewer.preview_async(buffer.text)
        if buffer.document == document:
            ip.pt_app.bottom_toolbar = preview
            get_app().invalidate()
        else: # text has changed, retry
            raise _Retry

    return async_previewer

def text_changed_handler(buffer):
    get_app().create_background_task(buffer._async_previewer())

def load_ipython_extension(ip:IPython.InteractiveShell):
    if ip.pt_app is None:
        print('No prompt application for this session, load preview failed')
        return
    ip.previewer = Previewer(ip)
    ip.events.register('pre_run_cell', ip.previewer.pre_run_cell)
    ip.events.register('post_run_cell', ip.previewer.post_run_cell)
    ip.pt_app.default_buffer._async_previewer = create_preview_coroutine(ip, ip.pt_app.default_buffer, ip.previewer)
    ip.pt_app.default_buffer.on_text_changed.add_handler(text_changed_handler)

def unload_ipython_extension(ip:IPython.InteractiveShell):
    ip.events.unregister('pre_run_cell', ip.previewer.pre_run_cell)
    ip.events.unregister('post_run_cell', ip.previewer.post_run_cell)
    ip.pt_app.default_buffer.on_text_changed.remove_handler(text_changed_handler)
    del ip.pt_app.default_buffer._async_previewer
    del ip.previewer
