#!/usr/bin/env python3
from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution('calcpy').version
except DistributionNotFound:
    __version__ = '0.0.0'

CALCPY_PROFILE_NAME = 'calcpy'

import IPython
import IPython.lib.backgroundjobs
import traitlets
import sympy
import platform
import sys
import importlib
import shutil

import calcpy.currency
import calcpy.formatters
import calcpy.transformers
import calcpy.info
import calcpy.autostore

def show_usage():
    print('''CalcPy - https://github.com/idanpa/calcpy''')

@IPython.core.magic.magics_class
class CalcPy(IPython.core.magic.Magics):
    debug = traitlets.Bool(False, config=True)
    implicit_multiply = traitlets.Bool(True, config=True)
    auto_solve = traitlets.Bool(True, config=True)
    caret_power = traitlets.Bool(False, config=True)
    auto_lambda = traitlets.Bool(True, config=True)
    auto_store_vars = traitlets.Bool(True, config=True)
    auto_matrix = traitlets.Bool(True, config=True)
    auto_date = traitlets.Bool(False, config=True)
    parse_latex = traitlets.Bool(True, config=True)
    bitwidth = traitlets.Int(0, config=True)
    precision = property(
        lambda calcpy: calcpy.shell.run_line_magic('precision', ''),
        lambda calcpy, p: calcpy.shell.run_line_magic('precision', p))

    def __init__(self, shell=None, **kwargs):
        super(CalcPy, self).__init__(shell, **kwargs)

def load_ipython_extension(ip:IPython.InteractiveShell):
    if ip.profile != CALCPY_PROFILE_NAME:
        print(f"warning: Not using the pycalc profile (current profile is {ip.profile}")

    ip.calcpy = CalcPy(ip)
    ip.push({'calcpy': ip.calcpy}, interactive=False)

    ip.register_magics(ip.calcpy) # register_magics loads the traitlets configuration

    if isinstance(ip.config.InteractiveShellApp.code_to_run, traitlets.config.loader.LazyConfigValue):
        print(f"CalcPy {__version__} (Python {platform.python_version()} IPython {IPython.__version__} SymPy {sympy.__version__}) ('??' for help)")
    ip.calcpy.jobs = IPython.lib.backgroundjobs.BackgroundJobManager()

    ip.show_usage = show_usage

    ip.push(importlib.import_module('calcpy.user').__dict__, interactive=False)
    try:
        ip.enable_pylab(gui='qt', import_all=False)
    except ImportError:
        pass # no gui

    calcpy.formatters.init(ip)
    calcpy.transformers.init(ip)
    calcpy.currency.init(ip)
    calcpy.info.init(ip)
    calcpy.autostore.init(ip)
    if callable(ip.user_ns.get('user_startup', None)):
        ip.ev('user_startup()')

if __name__ == '__main__':
    load_ipython_extension(IPython.get_ipython())
