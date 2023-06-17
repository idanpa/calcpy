import IPython
import inspect
import types
import sys
import os

class Autostore():
    def __init__(self, shell):
        self.shell = shell
        self.debug = False
        self.last_user_ns = []

        self.shell.events.register('post_run_cell', self.post_run_cell)

        for var_path in self.shell.db.keys('autostore/*'):
            var_name = os.path.basename(var_path)
            try:
                var = self.shell.db[var_path]
            except KeyError:
                print(f'Failed to restore "{var_path}": {sys.exc_info()[0]}, discarding')
                del self.shell.db[var_path]
            else:
                if var_name.startswith('_func_'):
                    # to allow %edit func_name, need to place function in file
                    file_path = self.shell.mktempfile(var, prefix='autostore' + var_name + '_')
                    self.shell.user_ns['__file__'] = file_path
                    try:
                        self.shell.safe_execfile(file_path, shell.user_ns, shell_futures=True, raise_exceptions=True)
                    except Exception as e:
                        print(f'Autostore - failed to restore function:\n{var}\n{repr(e)}\n\ndiscarding')
                        del self.shell.db[var_path]
                else:
                    self.shell.user_ns[var_name] = var

    def unload(self):
        self.shell.events.unregister('post_run_cell', self.post_run_cell)

    def store(self, var_name, verbose=True):
        var = self.shell.user_ns[var_name]
        if type(var) in [types.ModuleType, type]:
            return False

        if type(var) == types.FunctionType:
            try:
                # skip functions that were not defined by user in a cell or by %edit:
                var_file = inspect.getfile(var)
                if not (var_file.startswith('<ipython-input-') or ('autostore_func_' in var_file) or ('ipython_edit_' in var_file)):
                    return False
            except TypeError:
                return False
            try:
                var = inspect.getsource(var)
            except Exception as e:
                if verbose:
                    print(f'Failed to get function source {var_name}: {repr(e)}')
                return False
            var_name = '_func_' + var_name

        var_path = 'autostore/' + var_name
        try:
            self.shell.db[var_path] = var
        except Exception as e:
            if verbose:
                print(f'Failed to store {var_name}={var} of type {type(var)}: {repr(e)}')
            del self.shell.db[var_path]
            return False
        return True

    def remove(self, var_name, verbose=True):
        self.shell.db.pop('autostore/' + var_name, None)
        self.shell.db.pop('autostore/_func_' + var_name, None)

    def store_all_user_vars(self):
        new_last_user_ns = []
        for var_name in list(self.shell.user_ns):
            if var_name.startswith('_') or \
            var_name in self.shell.user_ns_hidden:
                continue
            self.store(var_name, verbose=self.debug)
            new_last_user_ns.append(var_name)
            if var_name in self.last_user_ns:
                self.last_user_ns.remove(var_name)

        for var_name in self.last_user_ns:
            self.remove(var_name)
        self.last_user_ns = new_last_user_ns

    def post_run_cell(self, result):
        self.store_all_user_vars()

    def reset(self):
        for var_path in self.shell.db.keys('autostore/*'):
            del self.shell.db[var_path]

        for var_name in list(self.shell.user_ns.keys()):
            if var_name.startswith('_') or \
            var_name in self.shell.user_ns_hidden:
                continue
            del self.shell.user_ns[var_name]

def load_ipython_extension(ip:IPython.InteractiveShell):
    ip.autostore = Autostore(ip)

def unload_ipython_extension(ip:IPython.InteractiveShell):
    ip.autostore.unload()

if __name__ == '__main__':
    load_ipython_extension(IPython.get_ipython())
