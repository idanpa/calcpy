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
import logging
import types
import sys
from functools import partial
import importlib
import shutil
from contextlib import redirect_stdout

import calcpy.currency
import calcpy.formatters
import calcpy.transformers

logger = logging.getLogger('calcpy')
debug = logger.debug

def show_usage():
    print('''CalcPy - https://github.com/idanpa/calcpy''')

@IPython.core.magic.magics_class
class CalcPy(IPython.core.magic.Magics):
    debug = traitlets.Bool(False, config=True)
    implicit_multiply = traitlets.Bool(True, config=True)
    auto_lambda = traitlets.Bool(True, config=True)
    auto_prev_ans = traitlets.Bool(True, config=True)
    auto_store_vars = traitlets.Bool(True, config=True)
    auto_matrix = traitlets.Bool(True, config=True)
    auto_date = traitlets.Bool(True, config=True)
    parse_latex = traitlets.Bool(True, config=True)
    bitwidth = traitlets.Int(0, config=True)

    def __init__(self, shell=None, **kwargs):
        super(CalcPy, self).__init__(shell, **kwargs)
        self.init_state = 0
        self.info_asked = False

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
            debug(f'Storing variable {variable_name}={ip.user_ns[variable_name]} of type {type(ip.user_ns[variable_name])}\n'+
                  f'failed with: {e}')
            ip.run_line_magic('store', f'-d {variable_name}')

def post_run_cell(result:IPython.core.interactiveshell.ExecutionResult, ip):
    ip = IPython.get_ipython()
    if ip.calcpy.auto_store_vars:
        store_all_user_vars(IPython.get_ipython())
    if ip.calcpy.info_asked and result.success and result.result is not None:
        ip.calcpy.jobs.new(print_more_info, result.result, daemon=True)

def print_more_info(res):
    terminal_size = shutil.get_terminal_size()
    page = terminal_size.columns * terminal_size.lines
    try:
        if isinstance(res, sympy.Expr):
            if len(res.free_symbols) == 1:
                sym = list(res.free_symbols)[0]
                print(f'\n{sympy.printing.pretty(sympy.diff(res))} = diff(_)')
                integral = sympy.integrate(res)
                if integral != sympy.Integral(res):
                    print(f'\n{sympy.printing.pretty(integral)} = integrate(_)')
                periodic = sympy.periodicity(res, sym)
                if periodic is not None:
                    print(f'\n{sympy.printing.pretty(periodic)} = periodic(_, {sym})')
            elif len(res.free_symbols) > 1:
                for sym in res.free_symbols:
                    print(f'\n{sympy.printing.pretty(sympy.diff(res, sym))} = diff(_, {sym})')
                for sym in res.free_symbols:
                    print(f'\n{sympy.printing.pretty(sympy.integrate(res, sym))} = integrate(_, {sym})')
                for sym in res.free_symbols:
                    periodic = sympy.periodicity(res, sym)
                    if periodic is not None:
                        print(f'\n{sympy.printing.pretty(periodic)} = periodic(_, {sym})')

            try:
                for sym in res.free_symbols:
                    print(f'\n{sympy.printing.pretty(sympy.calculus.util.minimum(res, sym))} = calculus.util.minimum(_, {sym})')
                    print(f'{sympy.printing.pretty(sympy.calculus.util.maximum(res, sym))} = calculus.util.maximum(_, {sym})')
            except:
                pass

            try:
                for sym in res.free_symbols:
                    print(f'\n{sympy.printing.pretty(sympy.calculus.util.continuous_domain(res, sym, sympy.S.Reals))} = calculus.util.continuous_domain(_, {sym}, S.Reals)')
                    print(f'\n{sympy.printing.pretty(sympy.calculus.util.function_range(res, sym, sympy.S.Reals))} = calculus.util.function_range(_, {sym}, S.Reals)')
            except:
                pass

            if len(res.free_symbols) > 0:
                solutions = sympy.solve(res)
                solutions_print = sympy.printing.pretty(solutions)
                if len(solutions_print) > page:
                    solutions_print = sympy.printing.pretty(list(map(sympy.N, solutions)))
                print(f'\n{solutions_print} = solve(_)')

            simple = sympy.simplify(res)
            if simple != res:
                print(f'\n{sympy.printing.pretty(sympy.simplify(res))} = simplify(_)')
        elif isinstance(res, sympy.matrices.common.MatrixCommon):
            if res.rows == res.cols:
                print(f'\n{sympy.printing.pretty(sympy.det(res))} = det(_)')
                print(f'{sympy.printing.pretty(sympy.trace(res))} = trace(_)')
                try:
                    print(f'\n{sympy.printing.pretty(res**-1)} = _**-1')
                except:
                    pass
                print(f'\n{sympy.printing.pretty(res.charpoly().as_expr())} = _.charpoly().as_expr()')
                evs = res.eigenvects()
                evs_print = sympy.printing.pretty(evs)
                if len(evs_print) > page:
                    evs = [(sympy.N(ev[0]), ev[1], tuple(map(sympy.N, ev[2]))) for ev in evs]
                    evs_print = sympy.printing.pretty(evs)
                print(f'\n{evs_print} = _.eigenvects() # ((eval, mult, evec),...')
                diag = res.diagonalize()
                diag_print = sympy.printing.pretty(diag)
                if len(diag_print) > page:
                    diag_print = sympy.printing.pretty(list(map(sympy.N, diag)))
                print(f'\n{diag_print} = _.diagonalize() # (P,D) with _==PDP^-1')
            else:
                print(f'\n{sympy.printing.pretty(sympy.rank(res))} = rank(_)')
                print(f'\n{sympy.printing.pretty(res.pinv())} = _.pinv()')
        elif isinstance(res, (list, tuple)):
            pass
        elif isinstance(res, (float, sympy.core.numbers.Float)):
            print(f'\n{sympy.printing.pretty(sympy.Rational(res))} = Rational(_)')
        elif isinstance(res, (complex, sympy.core.numbers.Float)):
            pass
        elif isinstance(res, (int, sympy.core.numbers.Integer)):
            f_dict = sympy.factorint(res)
            f_expr = None
            for base, expo in f_dict.items():
                pow = sympy.Pow(base, expo, evaluate=False)
                if f_expr is None:
                    f_expr = pow
                else:
                    f_expr = sympy.Mul(f_expr, pow, evaluate=False)
            print(f'\n{sympy.printing.pretty(f_expr)}       {sympy.printing.pretty(f_dict)} = _.factorint()')
        elif res is not None:
            try:
                res = sympy.sympify(res)
                print_more_info(res)
            except sympy.SympifyError:
                pass

    except Exception as e:
        print(e)

def load_ipython_extension(ip:IPython.InteractiveShell):
    if ip.profile != CALCPY_PROFILE_NAME:
        print(f"warning: Not using the pycalc profile (current profile is {ip.profile}")

    ip.calcpy = CalcPy(ip)
    ip.push({'calcpy': ip.calcpy}, interactive=False)
    # this is where the configuration is loaded:
    ip.register_magics(ip.calcpy)

    if isinstance(ip.config.InteractiveShellApp.code_to_run, traitlets.config.loader.LazyConfigValue): # better way to check this?
        print(f"CalcPy {__version__} (Python {platform.python_version()} IPython {IPython.__version__} SymPy {sympy.__version__}) ('??' for help)")
    ip.calcpy.jobs = IPython.lib.backgroundjobs.BackgroundJobManager()

    # logging:
    sh = logging.StreamHandler()
    sh.addFilter(logging.Filter('calcpy'))
    if ip.calcpy.debug:
        sh.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    logger.addHandler(sh)

    ip.show_usage = show_usage

    # init user
    ip.push(importlib.import_module('calcpy.user').__dict__, interactive=False)
    ip.enable_pylab(import_all=False)
    sympy.interactive.printing.init_printing(
        pretty_print=True,
        use_latex='mathjax',
        num_columns=shutil.get_terminal_size().columns,
        ip=ip)

    calcpy.formatters.init(ip)
    calcpy.transformers.init(ip)
    calcpy.currency.init(ip)

    ip.calcpy.jobs.new(calcpy.currency.update_currency_job, ip, daemon=True)

    ip.events.register('post_run_cell', partial(post_run_cell, ip=ip))

    # terminal title:
    sys.stdout.write("\x1b]2;CalcPy\x07")

    ip.calcpy.init_state = 1

if __name__ == '__main__':
    load_ipython_extension(IPython.get_ipython())
