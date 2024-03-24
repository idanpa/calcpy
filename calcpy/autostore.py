import IPython
import inspect
from time import perf_counter
import os

TIME_WARNING_SEC = 2

class Autostore():
    def __init__(self, shell, verbose=False):
        t = perf_counter()
        self.shell = shell
        self.verbose = verbose
        self.last_user_ns = []

        self.shell.events.register('post_run_cell', self.post_run_cell)

        for var_path in self.shell.db.keys('autostore/*'):
            var_name = os.path.basename(var_path)
            try:
                var = self.shell.db[var_path]
            except KeyError as e:
                print(f'Autostore: failed to restore "{var_name}" {repr(e)}')
                del self.shell.db[var_path]
                continue
            if var_name.startswith('_func_'):
                # to allow %edit func_name, need to place function in file
                file_path = self.shell.mktempfile(var, prefix='autostore' + var_name + '_')
                try:
                    self.shell.safe_execfile(file_path, shell.user_ns, shell_futures=True, raise_exceptions=True)
                except Exception as e:
                    print(f'Autostore: failed to restore function\n{var}\n{repr(e)}')
                    del self.shell.db[var_path]
                try:
                    self.shell.previewer.run_cell(var)
                except AttributeError:
                    pass
            else:
                if var_name in self.shell.user_ns:
                    print(f'Autostore: attempt to restore existing variable "{var_name}"')
                    del self.shell.db[var_path]
                else:
                    self.shell.user_ns[var_name] = var
        if perf_counter() - t > TIME_WARNING_SEC:
            print(f'Autostore took {perf_counter() - t:.3f}s! consider clearing unused vars')

    def unload(self):
        self.shell.events.unregister('post_run_cell', self.post_run_cell)

    def store(self, var_name, verbose=True):
        var = self.shell.user_ns[var_name]
        if inspect.isbuiltin(var) or inspect.ismodule(var) or inspect.isclass(var):
            return False
        if inspect.isfunction(var):
            # skip external functions:
            var_file = inspect.getfile(var)
            if not (var_file.startswith('<ipython-input-') or ('autostore_func_' in var_file) or ('ipython_edit_' in var_file)):
                return False
            try:
                var = inspect.getsource(var)
            except Exception as e:
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
             self.shell.user_ns[var_name] is \
              self.shell.user_ns_hidden.get(var_name, None):
                continue
            self.store(var_name, verbose=self.verbose)
            new_last_user_ns.append(var_name)
            if var_name in self.last_user_ns:
                self.last_user_ns.remove(var_name)

        for var_name in self.last_user_ns:
            self.remove(var_name)
        self.last_user_ns = new_last_user_ns

    def post_run_cell(self, result):
        self.store_all_user_vars()

    def _get_stored(self):
        return [os.path.basename(var_path).removeprefix('_func_') for \
                var_path in self.shell.db.keys('autostore/*')]

    def reset(self, prompt=True):
        if prompt:
            if input("Delete all variables [y/N] ").lower() not in ["y","yes"]:
                return
        for var_path in self.shell.db.keys('autostore/*'):
            self.shell.db.pop(var_path, None)
            self.shell.user_ns.pop(os.path.basename(var_path).removeprefix('_func_'), None)

def load_ipython_extension(ip:IPython.InteractiveShell, verbose=False):
    ip.autostore = Autostore(ip, verbose=verbose)

def unload_ipython_extension(ip:IPython.InteractiveShell):
    ip.autostore.unload()

if __name__ == '__main__':
    load_ipython_extension(IPython.get_ipython())
