from functools import partial
import os
import types
import IPython
import inspect
import sys

def store(ip:IPython.InteractiveShell, var_name, verbose=True):
        var = ip.user_ns[var_name]
        if type(var) in [types.ModuleType, type]:
            return False

        if type(var) == types.FunctionType:
            try:
                var = inspect.getsource(var)
            except Exception as e:
                if verbose:
                    print(f'Failed to get function source {var_name}: {repr(e)}')
                return False
            var_name = '_func_' + var_name

        var_path = 'autostore/' + var_name
        try:
            ip.db[var_path] = var
        except Exception as e:
            if verbose:
                print(f'Failed to store {var_name}={var} of type {type(var)}: {repr(e)}')
            del ip.db[var_path]
            return False
        return True

def remove(ip:IPython.InteractiveShell, var_name, verbose=True):
        ip.db.pop('autostore/' + var_name, None)
        ip.db.pop('autostore/_func_' + var_name, None)

last_user_ns = []
def store_all_user_vars(ip:IPython.InteractiveShell):
    global last_user_ns
    new_last_user_ns = []
    for var_name in ip.user_ns:
        if var_name.startswith('_') or \
           var_name in ip.user_ns_hidden:
            continue
        store(ip, var_name, verbose=ip.calcpy.debug)
        new_last_user_ns.append(var_name)
        if var_name in last_user_ns:
            last_user_ns.remove(var_name)

    for var_name in last_user_ns:
        remove(ip, var_name)
    last_user_ns = new_last_user_ns

def post_run_cell(result:IPython.core.interactiveshell.ExecutionResult, ip):
    if ip.calcpy.auto_store_vars:
        store_all_user_vars(ip)

def init(ip: IPython.InteractiveShell):
    ip.calcpy.init_state = 1
    ip.events.register('post_run_cell', partial(post_run_cell, ip=ip))

    for var_path in ip.db.keys('autostore/*'):
        var_name = os.path.basename(var_path)
        try:
            var = ip.db[var_path]
        except KeyError:
            print(f'Failed to restore "{var_path}": {sys.exc_info()[0]}')
            del ip.db[var_path]
        else:
            if var_name.startswith('_func_'):
                # run as cell so it would be possible to retreive source code
                ip.run_cell(var)
            else:
                ip.user_ns[var_name] = var


