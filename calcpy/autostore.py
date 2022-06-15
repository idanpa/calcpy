from functools import partial
import types
from contextlib import redirect_stdout
import IPython

def store_all_user_vars(ip:IPython.InteractiveShell):
    # defer variable store only when init is done
    if ip.calcpy.init_state == 0:
        return
    if ip.calcpy.init_state == 1:
        ip.calcpy.init_state = 2
        return
    who_ls = ip.run_line_magic('who_ls', '')

    for variable_name in who_ls:
        t = type(ip.user_ns[variable_name])
        if t in [types.FunctionType, types.ModuleType, type]:
            continue
        try:
            with redirect_stdout(None): # can't stop store from printing
                ip.run_line_magic('store', f'{variable_name}')
        except Exception as e:
            if ip.calcpy.debug:
                print(f'Storing variable {variable_name}={ip.user_ns[variable_name]} of type {type(ip.user_ns[variable_name])}\n'+
                      f'failed with: {e}')
            ip.run_line_magic('store', f'-d {variable_name}')

def post_run_cell(result:IPython.core.interactiveshell.ExecutionResult, ip):
    if ip.calcpy.auto_store_vars:
        store_all_user_vars(ip)

def init(ip: IPython.InteractiveShell):
    ip.calcpy.init_state = 1
    ip.events.register('post_run_cell', partial(post_run_cell, ip=ip))

