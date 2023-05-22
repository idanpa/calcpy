from functools import partial
import os
import types
import IPython
import inspect
import sys

def store(ip:IPython.InteractiveShell, variable_name, verbose=True):
        variable = ip.user_ns[variable_name]
        variable_type = type(variable)
        if variable_type in [types.ModuleType, type]:
            return False

        if variable_type == types.FunctionType:
            variable_path = 'autostore_func/' + variable_name
            variable = inspect.getsource(variable)
        else:
            variable_path = 'autostore/' + variable_name

        try:
            ip.db[variable_path] = variable
        except Exception as e:
            if verbose:
                print(f'Failed to store {variable_name}={variable} of type {variable_type}: {repr(e)}')
            del ip.db[variable_path]
            return False
        return True

def store_all_user_vars(ip:IPython.InteractiveShell):
    for variable_name in ip.user_ns:
        if variable_name.startswith('_') or \
           variable_name in ip.user_ns_hidden:
            continue
        store(ip, variable_name, verbose=ip.calcpy.debug)

def post_run_cell(result:IPython.core.interactiveshell.ExecutionResult, ip):
    if ip.calcpy.auto_store_vars:
        store_all_user_vars(ip)
    # TODO: delete variables that were deleted with del

def init(ip: IPython.InteractiveShell):
    ip.calcpy.init_state = 1
    ip.events.register('post_run_cell', partial(post_run_cell, ip=ip))

    for func_path in ip.db.keys('autostore_func/*'):
        try:
            func_code = ip.db[func_path]
        except KeyError:
            print(f'Failed to restore "{func_path}": {sys.exc_info()[0]}')
            del ip.db[func_path]
        else:
            # run as cell so it would be possible to retreive source code
            ip.run_cell(func_code)

    for variable_path in ip.db.keys('autostore/*'):
        variable_name = os.path.basename(variable_path)
        try:
            variable = ip.db[variable_path]
        except KeyError:
            print(f'Failed to restore "{func_path}": {sys.exc_info()[0]}')
            del ip.db[variable_path]
        else:
            ip.user_ns[variable_name] = variable


