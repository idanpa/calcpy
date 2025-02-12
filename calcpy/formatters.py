from functools import partial
import re
import shutil
import datetime
import IPython
import IPython.lib.pretty
import numpy
import sympy
import sympy.combinatorics
from sympy.printing.pretty.pretty import PrettyPrinter
from sympy.printing.pretty.stringpict import stringPict, prettyForm
from sympy.concrete.expr_with_limits import ExprWithLimits

MAX_SEQ_LENGTH = 100

def _bin_pad(bin_string, pad_every=4):
        return ' '.join(bin_string[i:i+pad_every] for i in range(0, len(bin_string), pad_every))

def _bin(integer, bitwidth):
    return _bin_pad(format(integer, f'0{bitwidth}b'))

def _hex(integer, bitwidth):
    hexwidth = (bitwidth + 3) // 4
    return '0x' + format(integer, f'0{hexwidth}x')

def _twos_complement_to_int(machine_integer, bitwidth):
    last_bit = 1 << (bitwidth-1)
    return -(machine_integer & last_bit) | (machine_integer & (last_bit-1))

def bin2int(binary_str):
    binary_str = binary_str.replace(' ', '')
    return _twos_complement_to_int(int(binary_str, 2), len(binary_str))

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
                if (-(1 << (bitwidth-1))) <= integer <= ((1 << (bitwidth-1))-1):
                        break
        # python bitwise is already acting on the two's complement
        machine_integer = integer & ((1 << bitwidth) - 1)

        of = ' '
        if _twos_complement_to_int(machine_integer, bitwidth) != integer:
            of = '≠'

        printer.text(f'{integer:<12} {of}{_hex(machine_integer, bitwidth):<15} {of}{_bin(machine_integer, bitwidth)}')

def complex_formatter(c, printer, cycle):
    printer.text(c.__repr__().strip('()').replace('j','i'))

def datetime_formatter(dt, printer, cycle):
    printer.text(dt.isoformat())

def timedelta_formatter(td, printer, cycle):
    printer.text(str(td))

def str_formatter(s, printer, cycle):
    if not (''.join(s.split())).isprintable():
        s = repr(s)
    printer.text(s)

def bytes_formatter(bs, printer, cycle):
    printer.text(str(bs) + ' = ' + ','.join(f'0x{b:02x}' for b in bs))

def integer_to_unicode_power(integer):
    s = ''
    neg = ''
    i2u = [0x2070,0x00b9,0x00b2,0x00b3,0x2074,0x2075,0x2076,0x2077,0x2078,0x2079]
    if integer < 0:
        neg = chr(0x207b)
        integer = -integer
    while integer > 0:
        s += chr(i2u[integer%10])
        integer //= 10
    return neg + s[::-1]

def ip_sympy_pretty_if_oneline_formatter(obj, printer, cycle):
    pp = PrettyPrinter()
    _print_Pow = pp._print_Pow
    def _print_Pow_unicode(power):
        b, e = power.as_base_exp()
        if isinstance(e, sympy.Integer):
            b = pp._print(b)
            if b.height() == 1:
                if b.binding > prettyForm.MUL and b.binding != prettyForm.NEG:
                    b = stringPict(*b.parens())
                return prettyForm(*b.right(stringPict(integer_to_unicode_power(e))))
        return _print_Pow(power)
    pp._print_Pow = _print_Pow_unicode

    obj_sympy_pretty = pp.doprint(obj)
    if '\n' in obj_sympy_pretty:
        printer.text(repr(obj))
    else:
        printer.text(obj_sympy_pretty)

def ip_matrix_formatter(m, printer, cycle):
    printer.text(str(tuple(tuple(x) for x in m.tolist())))

def ip_permutation_formatter(p, printer, cycle):
    printer.text(sympy.printing.pretty(sympy.combinatorics.Cycle(p)))

def pretty_stack(str1, relation, str2, num_columns):
    sp1 = stringPict(str1)
    sp1.baseline = sp1.height()//2
    sp2 = stringPict(str2)
    sp2.baseline = sp2.height()//2

    if sp1.width() > .75*num_columns or \
       sp2.width() + len(relation) > .75*num_columns  or \
       sp1.width() + len(relation) + sp2.width() > num_columns:
        return sp1.render(wrap_line=True, num_columns=num_columns) + f'\n{relation}\n' + \
               sp2.render(wrap_line=True, num_columns=num_columns)
    else:
        sp2 = stringPict(*sp2.left(relation))
        return stringPict(*sp1.right(sp2)).render(wrap_line=True, num_columns=num_columns)

def evalf(expr):
    calcpy = IPython.get_ipython().calcpy
    if calcpy.auto_evalf:
        expr = expr.doit()
    if isinstance(expr, sympy.matrices.MatrixBase):
        return expr.applyfunc(evalf)
    elif expr.free_symbols:
        if expr.is_polynomial() and calcpy.auto_expand_factor_poly:
            expand = expr.expand()
            if expand == expr:
                factor = expr.factor()
                if factor == expr:
                    return expr.simplify()
                return factor
            return expand
        elif expr.is_algebraic_expr():
            return expr.simplify()
        return expr
    else:
        expr = expr.simplify()
    types = set(map(type, expr.atoms(sympy.Rational, sympy.Function, sympy.NumberSymbol, ExprWithLimits)))
    types -= {sympy.Integer, sympy.core.numbers.Zero, sympy.core.numbers.One, sympy.core.numbers.NegativeOne}
    # call evalf only when needed - fractions, functions (e.g. trigonometric), constants (e.g. pi) or limits
    if calcpy.auto_evalf and types:
        return expr.evalf(chop=calcpy.chop, n=15)
    return expr

def evalf_iterable(iterable):
    evalu = []
    for idx, el in enumerate(iterable):
        if idx > MAX_SEQ_LENGTH:
            evalu.append('...')
            break
        if isinstance(el, sympy.Expr):
            evalu.append(evalf(el))
        elif isinstance(el, (list, tuple)):
            evalu.append(evalf_iterable(el))
        else:
            evalu.append(el)

    if isinstance(iterable, tuple):
        evalu = tuple(evalu)

    return evalu

def pretty(obj, n_col=None, n_row=None):
    if n_col is None or n_row is None:
        n_col, n_row = shutil.get_terminal_size()
    try: # pretty may fail on clashes with other class names
        sympy_pretty = sympy.printing.pretty(obj, num_columns=n_col)
    except:
        sympy_pretty = str(obj)
    if sympy_pretty.count('\n') >= n_row*1.5:
        ipython_pretty = IPython.lib.pretty.pretty(obj, max_width=n_col)
        if ipython_pretty.count('\n') < n_row*1.5:
            return ipython_pretty
    return sympy_pretty

def iterable_formatter(iterable, printer, cycle):
    n_col, n_row = shutil.get_terminal_size()

    if len(iterable) > MAX_SEQ_LENGTH+1:
        iterable = iterable[:MAX_SEQ_LENGTH+1]
        iterable[MAX_SEQ_LENGTH] = '...'

    pretty_s = pretty(iterable, n_col, n_row)
    out = pretty_s

    try:
        evalu_s = pretty(evalf_iterable(iterable), n_col, n_row)
        if evalu_s != pretty_s:
            out = pretty_stack(out, " ≈ ", evalu_s, n_col)
    except Exception as e:
        if IPython.get_ipython().calcpy.debug:
            print(f'iterable formatter failed: {e}')

    printer.text(out)

def evalf_dict(d):
    evalf_d = {}
    for key in d:
        if isinstance(key, sympy.Expr):
            evalf_key = evalf(key)
        else:
            evalf_key = key

        if isinstance(d[key], sympy.Expr):
            evalf_d[evalf_key] = evalf(d[key])
        else:
            evalf_d[evalf_key] = d[key]

    return evalf_d

def sympy_dict_formatter(d, printer, cycle):
    n_col, n_row = shutil.get_terminal_size()

    pretty_s = pretty(d, n_col, n_row)
    out = pretty_s

    try:
        evalf_dict_s = pretty(evalf_dict(d), n_col, n_row)
        if evalf_dict_s != pretty_s:
            out = pretty_stack(out, " ≈ ", evalf_dict_s, n_col)
    except Exception as e:
        if IPython.get_ipython().calcpy.debug:
            print(f'dictionary formatter failed: {e}')

    printer.text(out)

def sympy_expr_formatter(s, printer, cycle):
    n_col, n_row = shutil.get_terminal_size()

    pretty_s = pretty(s, n_col, n_row)
    out = pretty_s

    try:
        if not isinstance(s, (sympy.Integer, sympy.Float)):
            evalu_s = pretty(evalf(s), n_col, n_row)
            if evalu_s != pretty_s:
                out = pretty_stack(out, " ≈ ", evalu_s, n_col)
    except Exception as e:
        if IPython.get_ipython().calcpy.debug:
            print(f'expr formatter failed: {e}')

    printer.text(out)

def sympy_pretty_formatter(obj, printer, cycle):
    n_col, n_row = shutil.get_terminal_size()
    printer.text(sympy.printing.pretty(obj, num_columns=n_col))

def numpy_array_formatter(obj, printer, cycle):
    return sympy_expr_formatter(sympy.Matrix(obj), printer, cycle)

def previewer_formatter(obj):
    try:
        if isinstance(obj, sympy.Expr):
            obj_str = IPython.lib.pretty.pretty(obj)
            if not isinstance(obj, (sympy.Integer, sympy.Float)):
                evalu_obj = IPython.lib.pretty.pretty(evalf(obj))
                if obj_str != evalu_obj:
                    obj_str += " ≈ " + evalu_obj
        elif isinstance(obj, sympy.combinatorics.Cycle):
            obj_str = IPython.lib.pretty.pretty(obj)
        elif isinstance(obj, (list, tuple)):
            obj_str = IPython.lib.pretty.pretty(evalf_iterable(obj))
        elif isinstance(obj, dict):
            obj_str = IPython.lib.pretty.pretty(evalf_dict(obj))
        else:
            obj_str = IPython.lib.pretty.pretty(obj)
    except:
        obj_str = ''

    obj_str = re.sub(r'\s+', ' ', obj_str)
    num_columns = shutil.get_terminal_size().columns
    if len(obj_str) > num_columns:
        obj_str = obj_str[:num_columns-4] + '...'
    return obj_str

def init(ip: IPython.InteractiveShell):
    sympy.interactive.printing.init_printing(
        pretty_print=True,
        use_latex='mathjax',
        latex_mode='inline',
        use_unicode=not (ip.config.TerminalInteractiveShell.simple_prompt==True),
        num_columns=shutil.get_terminal_size().columns,
        ip=ip)

    IPython.lib.pretty.for_type(str, str_formatter)
    IPython.lib.pretty.for_type(complex, complex_formatter)
    IPython.lib.pretty.for_type(datetime.datetime, datetime_formatter)
    IPython.lib.pretty.for_type(datetime.timedelta, timedelta_formatter)
    IPython.lib.pretty.for_type(sympy.printing.defaults.Printable, ip_sympy_pretty_if_oneline_formatter)
    IPython.lib.pretty.for_type(sympy.matrices.MatrixBase, ip_matrix_formatter)
    IPython.lib.pretty.for_type(sympy.combinatorics.Cycle, sympy_pretty_formatter)
    IPython.lib.pretty.for_type(sympy.combinatorics.Permutation, ip_permutation_formatter)

    formatter = ip.display_formatter.formatters['text/plain']
    formatter.for_type(str, str_formatter)
    formatter.for_type(bytes, bytes_formatter)
    formatter.for_type(int, int_formatter)
    formatter.for_type(sympy.Integer, int_formatter)
    formatter.for_type(complex, complex_formatter)
    formatter.for_type(datetime.datetime, datetime_formatter)
    formatter.for_type(datetime.timedelta, timedelta_formatter)
    formatter.for_type(list, iterable_formatter)
    formatter.for_type(tuple, iterable_formatter)
    formatter.for_type(dict, sympy_dict_formatter)
    formatter.for_type(sympy.Expr, sympy_expr_formatter)
    formatter.for_type(sympy.matrices.MatrixBase, sympy_expr_formatter)
    formatter.for_type(sympy.core.function.FunctionClass, IPython.lib.pretty._function_pprint)
    formatter.for_type(sympy.combinatorics.Permutation, sympy_pretty_formatter)
    formatter.for_type(sympy.combinatorics.Cycle, sympy_pretty_formatter)
    formatter.for_type(numpy.ndarray, numpy_array_formatter)

    # use IPython's float precision
    def print_float(self, e):
        ipython = IPython.get_ipython()
        form = ipython.display_formatter.formatters['text/plain']
        return prettyForm(form.float_format % e)

    PrettyPrinter._print_Float = print_float
    PrettyPrinter._print_float = print_float

    # for sympy to support format specifiers:
    def integer__format__(self, format_spec):
        return int.__format__(int(self), format_spec)
    sympy.Integer.__format__ = integer__format__
    def rational__format__(self, format_spec):
        return float.__format__(float(self), format_spec)
    sympy.Rational.__format__ = rational__format__

