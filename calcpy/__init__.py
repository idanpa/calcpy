from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('calcpy')
except PackageNotFoundError:
    __version__ = 'no-package'

CALCPY_PROFILE_NAME = 'calcpy'

import IPython
import IPython.lib.backgroundjobs
import traitlets
import sympy
import platform
import json
import os
from contextlib import redirect_stdout

from . import currency
from . import formatters
from . import transformers
from . import info
from . import autostore
import previewer

def get_calcpy():
    return IPython.get_ipython().calcpy

@IPython.core.magic.magics_class
class CalcPy(IPython.core.magic.Magics):
    debug = traitlets.Bool(False, config=True)
    caret_power = traitlets.Bool(True, config=True, help="convert '^' to '**' and '^^' to '^'")
    auto_product = traitlets.Bool(True, config=True, help="implicit product, e.g. convert '2x' to '2*x'")
    auto_solve = traitlets.Bool(True, config=True, help="convert 'x+1=0' to solve(Eq(x+1,0))")
    auto_lambda = traitlets.Bool(True, config=True, help="convert 'f(x,y):=x+y' to 'f=lambda x,y : x+y'")
    auto_store = traitlets.Bool(True, config=True, help="enable automatic store/restore of variables and functions")
    auto_matrix = traitlets.Bool(True, config=True, help="convert tuples of tuples to matrices")
    auto_rational = traitlets.Bool(True, config=True, help="convert integer division and floats to rationals")
    auto_date = traitlets.Bool(True, config=True, help="convert 'd\"today\"' to datetime object")
    auto_symbols = traitlets.Bool(True, config=True, help="automatically consider single letter variables as symbols ('x','x_2','alpha')")
    auto_factorial = traitlets.Bool(True, config=True, help="convert '5!' to 'factorial(5)'")
    auto_permutation = traitlets.Bool(False, config=True, help="convert '(0 1)(3 4)' to 'Permutation(0, 1)(3, 4)'")
    auto_latex = traitlets.Bool(True, config=True, help="convert $1+1$ to parse_latex('1+1')")
    auto_latex_sub = traitlets.Bool(True, config=True, help="substitute local variables in parsed latex")
    previewer = traitlets.Bool(True, config=True, help="enable previewer")
    bitwidth = traitlets.Int(0, config=True, help="bitwidth of displayed binary integers, if 0 adjusted accordingly")
    chop = traitlets.Bool(True, config=True, help="replace small numbers with zero")
    eng_units_prefixes = traitlets.Bool(True, config=True, help="engineering units prefixes (e.g. 2k=2000)")
    precision = property(
        lambda calcpy: calcpy.shell.run_line_magic('precision', ''),
        lambda calcpy, p: calcpy.shell.run_line_magic('precision', p))

    _print_transformed_code = traitlets.Bool(False, config=False)

    def __init__(self, shell=None, **kwargs):
        ''''''
        super(CalcPy, self).__init__(shell, **kwargs)

        self._eng_units_prefixes_dict = { 'G': transformers.IntegerUnitPrefix(1e9), 'M': transformers.IntegerUnitPrefix(1e6), 'k': transformers.IntegerUnitPrefix(1e3),
            'm': transformers.PowUnitPrefix(10, -3),  'u': transformers.PowUnitPrefix(10, -6),  'n': transformers.PowUnitPrefix(10, -9), 'p': transformers.PowUnitPrefix(10, -12) }

        self.user_startup_path = os.path.join(shell.profile_dir.location, 'user_startup.py')
        config_path = os.path.join(self.shell.profile_dir.location, 'calcpy.json')
        if os.path.isfile(config_path):
            try:
                with open(config_path, 'r') as f:
                    for trait_name, value in json.load(f).items():
                        setattr(self, trait_name, value)
            except Exception as e:
                print(f'Failed to read config from {config_path}: {repr(e)}')

        def calcpy_trait_observe(change):
            try:
                with open(config_path, 'w') as f:
                    json.dump(self.non_default_config_values(), f, indent=1)
            except Exception as e:
                print(f'Failed to write config from {config_path}: {repr(e)}')
        self.observe(calcpy_trait_observe)

        def _auto_store_changed(change):
            if change.old != change.new == True:
                autostore.load_ipython_extension(self.shell)
            if change.old != change.new == False:
                autostore.unload_ipython_extension(self.shell)
        self.observe(_auto_store_changed, names='auto_store')

        def _previewer_changed(change):
            if change.old != change.new == True:
                self.load_previewer()
            if change.old != change.new == False:
                self.unload_previewer()
        self.observe(_previewer_changed, names='previewer')

        def _eng_units_prefixes_changed(change):
            if change.new == True:
                self.push(self._eng_units_prefixes_dict, interactive=False)
            if change.new == False:
                for key in self._eng_units_prefixes_dict:
                    self.shell.user_ns.pop(key, None)
                    self.shell.user_ns_hidden.pop(key, None)
        self.observe(_eng_units_prefixes_changed, names='eng_units_prefixes')

        CalcPy.__doc__ = "CalcPy\n"
        for trait_name, trait in sorted(self.traits(config=True).items()):
            CalcPy.__doc__ += self.class_get_trait_help(trait, None).replace('--CalcPy.', '') + '\n'

    def non_default_config_values(self):
        non_def = {}
        trait_defaults = self.trait_defaults(config=True)
        for trait_name, value in self.trait_values(config=True).items():
            if value != trait_defaults[trait_name]:
                non_def[trait_name] = value
        return non_def

    def push(self, variables, interactive=True):
        self.shell.push(variables, interactive)
        try:
            self.shell.previewer.push(variables)
        except AttributeError:
            pass

    def __repr__(self):
        config = self.trait_values(config=True)
        return 'CalcPy ' + repr(config)

    def edit_user_startup(self):
        self.shell.run_line_magic('edit', self.user_startup_path)

    def reset(self, prompt=True):
        if (not prompt) or (input("Reset CalcPy configuration? [y/N] ").lower() in ["y","yes"]):
            for trait_name, trait in sorted(self.traits(config=True).items()):
                setattr(self, trait_name, trait.default_value)
        self.shell.autostore.reset(prompt)

    def load_previewer(self):
        previewer_config = self.shell.config.copy()
        previewer_config.CalcPy.previewer = False
        previewer_config.CalcPy.auto_store = False
        previewer.load_ipython_extension(self.shell, config=previewer_config, formatter=formatters.previewer_formatter, debug=self.debug)

    def unload_previewer(self):
        previewer.unload_ipython_extension(self.shell)

def load_ipython_extension(ip:IPython.InteractiveShell):
    if ip.profile != CALCPY_PROFILE_NAME:
        print(f'warning: Not using the {CALCPY_PROFILE_NAME} profile (current profile is {ip.profile}')

    ip.calcpy = CalcPy(ip)
    ip.push({'calcpy': ip.calcpy}, interactive=False)

    if ip.calcpy.previewer and 'InteractiveShellApp.code_to_run' not in ip.config:
        ip.calcpy.load_previewer()

    ip.register_magics(ip.calcpy)

    ip.calcpy.jobs = IPython.lib.backgroundjobs.BackgroundJobManager()

    def show_usage():
        print(f'''CalcPy {__version__} (Python {platform.python_version()} IPython {IPython.__version__} SymPy {sympy.__version__})
https://github.com/idanpa/calcpy''')

    ip.show_usage = show_usage

    ip.run_cell('from calcpy.user import *', store_history=False)
    if ip.calcpy.eng_units_prefixes:
        ip.push(ip.calcpy._eng_units_prefixes_dict, interactive=False)

    try:
        with redirect_stdout(None): # some recent IPython version prints here
            ip.enable_pylab(import_all=False)
    except ImportError:
        pass # no gui

    formatters.init(ip)
    transformers.init(ip)
    info.init(ip)
    currency.init(ip)

    # we hide ourselves all initial variable, (instead of ipython InteractiveShellApp.hide_initial_ns)
    # so autostore and user startups variables would be exposed to who, who_ls
    ip.user_ns_hidden.update(ip.user_ns)

    if ip.calcpy.auto_store:
        autostore.load_ipython_extension(ip)

    if os.path.isfile(ip.calcpy.user_startup_path):
        ip.safe_execfile(ip.calcpy.user_startup_path,
                         ip.user_ns,
                         raise_exceptions=False,
                         shell_futures=True)

if __name__ == '__main__':
    load_ipython_extension(IPython.get_ipython())
