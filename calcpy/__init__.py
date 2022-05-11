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
import re
import logging
import types
import sys
import os
import ast
from functools import partial
import importlib
import requests
import shutil
import warnings
from time import sleep

try:
    import dateparser
    dateparsing = True
    import datetime
except ModuleNotFoundError:
    dateparsing = False

import calcpy.currency

logger = logging.getLogger('calcpy')
debug = logger.debug

def show_usage():
    print('''
CalcPy
''')

@IPython.core.magic.magics_class
class CalcPy(IPython.core.magic.Magics):
    debug = traitlets.Bool(False, config=True)
    implicit_multiply = traitlets.Bool(True, config=True)
    auto_lambda = traitlets.Bool(True, config=True)
    auto_prev_ans = traitlets.Bool(True, config=True)
    auto_store_vars = traitlets.Bool(True, config=True)
    parse_latex = traitlets.Bool(True, config=True)
    dateparser = traitlets.Bool(True, config=True)
    bitwidth = traitlets.Int(0, config=True)

    def __init__(self, shell=None, **kwargs):
        super(CalcPy, self).__init__(shell, **kwargs)
        self.init_state = 0
        self.info_asked = False

class DisablePrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

def _bin_pad(bin_string, pad_every=4):
        return ' '.join(bin_string[i:i+pad_every] for i in range(0, len(bin_string), pad_every))

def _bin(integer, bitwidth):
    return _bin_pad(format(integer, f'0{bitwidth}b'))

def _hex(integer, bitwidth):
    return hex(integer)

def int_formatter(integer, printer, cycle):
    ip = IPython.get_ipython()
    # avoid formatting inside list etc.:
    if len(printer.stack) > 1:
        printer.text(repr(integer))
    else:
        if ip.calcpy.bitwidth > 0:
            bitwidth = ip.calcpy.bitwidth
        else:
            for bitwidth in [8, 16, 32, 64, 128]:
                # TODO: fix for negative numbers:
                if (integer < (1 << bitwidth)):
                        break
        printer.text('{0:<13} {1:<16} {2}'.format(integer, _hex(integer, bitwidth), _bin(integer, bitwidth)))

def complex_formatter(c, printer, cycle):
    printer.text(c.__repr__().strip('()').replace('j','i'))

def datetime_formatter(dt, printer, cycle):
    printer.text(dt.isoformat())

def str_formatter(s, printer, cycle):
    printer.text(s)

def sympy_expr_formatter(s, printer, cycle):
    if isinstance(s, (sympy.core.numbers.Integer, sympy.core.numbers.Float)):
        printer.text(f'{sympy.printing.pretty(s)}')
    else:
        printer.text(f'{sympy.printing.pretty(s)} ≈ {sympy.N(s)}')

def calcpy_input_transformer_cleanup(lines):
    ip = IPython.get_ipython()
    if (lines[0] != '?' and lines[0][0] == '?'):
        ip.calcpy.info_asked = True
        lines[0] = lines[0][1:]
    else:
        ip.calcpy.info_asked = False
    return lines

def calcpy_input_transformer_post(lines):
    ip = IPython.get_ipython()
    var_p = r'[^\d\W]\w*' # match any valid variable name

    def re_sub_mult_replace(match, vars):
        if match[2] in vars:
            return f'{match[1]}*{match[2]}'
        return match[0]

    user_vars = list(ip.ev("locals().keys()"))
    for i in range(len(lines)):
        var_def_pattern = rf'^({var_p})\s*=(.*)'
        vars_match = re.match(var_def_pattern, lines[i])
        if vars_match:
            user_vars.append(vars_match[1])

        latex_pattern = rf'(\$[^$]*\$)'
        if ip.calcpy.parse_latex:
            latex_matches = re.findall(latex_pattern, lines[i])
        else:
            latex_matches = []
        latex_matches = set(latex_matches)
        # avoid processing of latex
        for match in latex_matches:
            lines[i] = lines[i].replace(match, f'({hash(match)})')

        if ip.calcpy.implicit_multiply: # asterisk-free multiplication: 4MB => 4*MB
            re_sub_mult_pattern = rf'(0x[0-9a-f]*|0X[0-9A-F]*|-?\d*\.?\d+e-?\d+|-?\d*\.?\d+)({var_p})'
            lines[i] = re.sub(re_sub_mult_pattern, partial(re_sub_mult_replace, vars=user_vars), lines[i])

        for match in latex_matches:
            lines[i] = lines[i].replace(f'({hash(match)})', f'parse_latex(r"{match[1:-1]}")')

    if ip.calcpy.auto_prev_ans: # auto substitute previous answer: * a => _ * a
        if lines[0][0] in ['+', '*', '/']: # '-' is ambiguous
            lines[0] = '_' + lines[0]

    def lambda_replace(match):
        return match[1] + '= lambda ' +  match[2] + ':' + match[3]

    if ip.calcpy.auto_lambda: # easier lambda: f(x,y) = x + y => f = lambda x, y : x + y
        lambda_pattern = rf'^({var_p})\((.*)\)\s*=([^=].*)'
        lines[0] = re.sub(lambda_pattern, lambda_replace, lines[0])

    return lines

class ReplaceIntegerDivisionWithRational(ast.NodeTransformer):
    def visit_BinOp(self, node):
        def is_integer(x):
            if isinstance(x, ast.Num) and isinstance(x.n, int):
                return True
            elif isinstance(x, ast.UnaryOp) and isinstance(x.op, (ast.USub, ast.UAdd)):
                return is_integer(x.operand)
            elif isinstance(x, ast.BinOp) and isinstance(x.op, (ast.Add, ast.Sub, ast.Mult, ast.Pow)):
                return is_integer(x.left) and is_integer(x.right)
            else:
                return False

        if (isinstance(node.op, ast.Div) and is_integer(node.left) and is_integer(node.right)):
            return ast.Call(func=ast.Name(id='Rational', ctx=ast.Load()),
                            args=[node.left, node.right], keywords=[])
        return self.generic_visit(node)

class ReplaceTupleWithMatrices(ast.NodeTransformer):
    def visit_Tuple(self, node):
        matrix_ast = ast.Call(func=ast.Name(id='Matrix', ctx=ast.Load()), args=[node], keywords=[])
        matrix_code = compile(ast.fix_missing_locations(ast.Expression(matrix_ast)), '<string>', 'eval')
        ip = IPython.get_ipython()

        # sympy would warn if there is a non expression object, use this warning to fallback:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                matrix = ip.ev(matrix_code)
        except:
            return self.generic_visit(node)

        return matrix_ast

class ReplaceStringsWithDates(ast.NodeTransformer):
    def visit_Constant(self, node):
        if isinstance(node, ast.Str):
            dt = dateparser.parse(node.s, settings={'STRICT_PARSING': True})
            if dt:
                return ast.Call(
                    func=ast.Attribute(value=ast.Name(id='datetime', ctx=ast.Load()), attr='datetime', ctx=ast.Load()),
                    args=[ast.Constant(value=dt.year), ast.Constant(value=dt.month), ast.Constant(value=dt.day),
                            ast.Constant(value=dt.hour), ast.Constant(value=dt.minute), ast.Constant(value=dt.second), ast.Constant(value=dt.microsecond)],
                    keywords=[])
        return self.generic_visit(node)

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
            with DisablePrints(): # can't stop store from printing
                ip.run_line_magic('store', f'{variable_name}')
        except Exception as e:
            debug(f'Storing variable {variable_name}={ip.user_ns[variable_name]} of type {type(ip.user_ns[variable_name])}\n'+
                  f'failed with: {e}')
            ip.run_line_magic('store', f'-d {variable_name}')

def post_run_cell(result:IPython.core.interactiveshell.ExecutionResult, ip, jobs):
    ip = IPython.get_ipython()
    if ip.calcpy.auto_store_vars:
        store_all_user_vars(IPython.get_ipython())
    if ip.calcpy.info_asked:
        jobs.new(print_more_info, ip, result.result, daemon=True)

def update_currency_job(ip:IPython.InteractiveShell):
    while True:
        try:
            calcpy.currency.set_rates(ip)
        except requests.exceptions.ConnectionError:
            pass  # offline
        except Exception as e:
            print(e)
        sleep(60*60*12)

def print_more_info(ip:IPython.InteractiveShell, result):
    try:
        if isinstance(result, sympy.core.expr.Expr):
            print(f'\n{sympy.printing.pretty(sympy.diff(result))} = diff(_)')
            print(f'\n{sympy.printing.pretty(sympy.integrate(result))} = integrate(_)')
            solutions = sympy.solve(result)
            terminal_size = shutil.get_terminal_size()
            page = terminal_size.columns * terminal_size.lines
            if len(sympy.printing.pretty(solutions)) < page:
                print(f'\n{sympy.printing.pretty(sympy.solve(result))} = solve(_)')
            else:
                print(f'\n{sympy.printing.pretty(list(map(sympy.N, solutions)))} = solve(_)')
            simple = sympy.simplify(result)
            if simple != result:
                print(f'\n{sympy.printing.pretty(sympy.simplify(result))} = simplify(_)')
        elif isinstance(result, sympy.matrices.common.MatrixCommon):
            if result.rows == result.cols:
                print(f'\n{sympy.printing.pretty(sympy.det(result))} = det(_)')
                print(f'{sympy.printing.pretty(sympy.trace(result))} = trace(_)')
                try:
                    print(f'\n{sympy.printing.pretty(result**-1)} = _**-1')
                except:
                    pass
                print(f'\n{sympy.printing.pretty(result.charpoly())} = _.charpoly()')
                print(f'\n{sympy.printing.pretty(result.eigenvects())} = _.eigenvects() # ((eval, mult, evec),...')
                print(f'\n{sympy.printing.pretty(result.diagonalize())} = _.diagonalize() # (P,D) with _==PDP^-1')
            else:
                print(f'\n{sympy.printing.pretty(sympy.rank(result))} = rank(_)')
                print(f'\n{sympy.printing.pretty(result.pinv())} = _.pinv()')

    except Exception as e:
        print(e)

def calcpy_monkey_patching(ip:IPython.InteractiveShell):
    ip.show_usage = show_usage

    def sympy_expr_call(self, *args):
        # single non-constant expression, interpret as product
        if len(args) == 1 and isinstance(args[0], sympy.core.expr.Expr) and not args[0].is_constant():
                return self.__rmul__(args[0])
        # else, substitute
        sorted_symbols = sorted(self.free_symbols, key=lambda s: s.name)
        if len(args) != len(sorted_symbols):
            raise TypeError(f'Expected {len(sorted_symbols)} arguments {sorted_symbols}')
        return self.subs(zip(sorted_symbols, args))

    sympy.core.expr.Expr.__call__ = sympy_expr_call

    sympy.core.expr.Expr.__xor__ = sympy.core.expr.Expr.__pow__
    sympy.core.expr.Expr.__rxor__ = sympy.core.expr.Expr.__rpow__

def load_ipython_extension(ip:IPython.InteractiveShell):
    if ip.profile != CALCPY_PROFILE_NAME:
        print(f"warning: Not using the pycalc profile (current profile is {ip.profile}")

    ip.calcpy = CalcPy(ip)
    ip.push({'calcpy': ip.calcpy})
    # this is where the configuration is loaded:
    ip.register_magics(ip.calcpy)

    if isinstance(ip.config.InteractiveShellApp.code_to_run, traitlets.config.loader.LazyConfigValue): # better way to check this?
        print(f"CalcPy {__version__} (Python {platform.python_version()} IPython {IPython.__version__}) ('??' for help)")
    jobs = IPython.lib.backgroundjobs.BackgroundJobManager()
    jobs.new(update_currency_job, ip, daemon=True)

    # logging:
    sh = logging.StreamHandler()
    sh.addFilter(logging.Filter('calcpy'))
    if ip.calcpy.debug:
        sh.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    logger.addHandler(sh)

    calcpy_monkey_patching(ip)

    # init user
    ip.push(importlib.import_module('calcpy.user').__dict__, interactive=False)
    ip.enable_pylab(import_all=False)
    sympy.interactive.printing.init_printing(
        pretty_print=True,
        use_latex='mathjax',
        num_columns=shutil.get_terminal_size().columns,
        ip=ip)

    # formatters (after sympy's init_printing)
    formatter = ip.display_formatter.formatters['text/plain']
    formatter.for_type(str, str_formatter)
    formatter.for_type(int, int_formatter)
    formatter.for_type(complex, complex_formatter)
    formatter.for_type(datetime.datetime, datetime_formatter)
    formatter.for_type(sympy.core.expr.Expr, sympy_expr_formatter)
    formatter.for_type(sympy.core.function.FunctionClass, IPython.lib.pretty._function_pprint)

    # transformers
    ip.ast_transformers.append(ReplaceIntegerDivisionWithRational())
    ip.ast_transformers.append(ReplaceTupleWithMatrices())
    if ip.calcpy.dateparser and dateparsing:
        ip.ast_transformers.append(ReplaceStringsWithDates())
    ip.input_transformers_cleanup.append(calcpy_input_transformer_cleanup)
    ip.input_transformers_post.append(calcpy_input_transformer_post)

    ip.events.register('post_run_cell', partial(post_run_cell, ip=ip, jobs=jobs))

    # terminal title:
    sys.stdout.write("\x1b]2;CalcPy\x07")

    ip.calcpy.init_state = 1

if __name__ == '__main__':
    load_ipython_extension(IPython.get_ipython())
