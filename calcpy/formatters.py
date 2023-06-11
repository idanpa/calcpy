from functools import partial
import shutil
import datetime
import IPython
import sympy
from sympy.printing.pretty.stringpict import stringPict

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
    printer.text(s)

def pretty_stack(str1, relation, str2, num_columns):
    sp1 = stringPict(str1)
    sp1.baseline = sp1.height()//2
    sp2 = stringPict(str2)
    sp2.baseline = sp2.height()//2
    sp2 = stringPict(*sp2.left(relation))

    if sp1.width() > .75*num_columns or \
       sp2.width() > .75*num_columns  or \
       sp1.width() + sp2.width() > num_columns:
        return sp1.render(wrap_line=True, num_columns=num_columns) + '\n\n' + \
               sp2.render(wrap_line=True, num_columns=num_columns)
    else:
        return stringPict(*sp1.right(sp2)).render(wrap_line=True, num_columns=num_columns)

def sympy_evalf_options():
    calcpy = IPython.get_ipython().calcpy
    return {
        'chop': calcpy.chop,
        'n': 15,
    }

def sympy_iterable_formatter(iterable, printer, cycle):
    num_columns = shutil.get_terminal_size().columns
    pretty = partial(sympy.printing.pretty, num_columns=num_columns)

    pretty_s = pretty(iterable)
    out = pretty_s

    try:
        options = sympy_evalf_options()
        evalu = [el.evalf(**options) if hasattr(el, 'evalf') else el for el in iterable]
        if isinstance(iterable, tuple):
            evalu = tuple(evalu)
        evalu_s = pretty(evalu)
        if evalu_s != pretty_s:
            out = pretty_stack(out, " ≈ ", evalu_s, num_columns)
    except Exception as e:
        if IPython.get_ipython().calcpy.debug:
            print(f'iterable formatter failed: {e}')

    printer.text(out)

def sympy_dict_formatter(dict, printer, cycle):
    num_columns = shutil.get_terminal_size().columns
    pretty = partial(sympy.printing.pretty, num_columns=num_columns)

    pretty_s = pretty(dict)
    out = pretty_s

    try:
        worth_printing = False
        evalf_dict = {}
        options = sympy_evalf_options()
        for key in dict:
            if hasattr(key, 'evalf'):
                evalf_key = key.evalf(**options)
                if pretty(evalf_key) != pretty(key):
                    worth_printing = True
            else:
                evalf_key = key

            if hasattr(dict[key], 'evalf'):
                evalf_dict[evalf_key] = dict[key].evalf(**options)
                if pretty(evalf_dict[evalf_key]) != pretty(dict[key]):
                    worth_printing = True
            else:
                evalf_dict[evalf_key] = dict[key]

        if worth_printing:
            out = pretty_stack(out, " ≈ ", pretty(evalf_dict), num_columns)
    except Exception as e:
        if IPython.get_ipython().calcpy.debug:
            print(f'dictionary formatter failed: {e}')

    printer.text(out)

def sympy_expr_formatter(s, printer, cycle):
    num_columns = shutil.get_terminal_size().columns
    pretty = partial(sympy.printing.pretty, num_columns=num_columns)

    pretty_s = pretty(s)
    out = pretty_s

    try:
        if not isinstance(s, (sympy.core.numbers.Integer, sympy.core.numbers.Float)):
            simpl = sympy.simplify(s)
            simpl_s = pretty(simpl)
            if simpl_s != pretty_s:
                out = pretty_stack(out, " = ", simpl_s, num_columns)

            evalu = simpl.evalf(**sympy_evalf_options())
            evalu_s = pretty(evalu)
            if evalu_s != simpl_s and evalu_s != pretty_s:
                out = pretty_stack(out, " ≈ ", evalu_s, num_columns)
    except Exception as e:
        if IPython.get_ipython().calcpy.debug:
            print(f'expr formatter failed: {e}')

    printer.text(out)

def init(ip: IPython.InteractiveShell):
    sympy.interactive.printing.init_printing(
        pretty_print=True,
        use_latex='mathjax',
        num_columns=shutil.get_terminal_size().columns,
        ip=ip)

    formatter = ip.display_formatter.formatters['text/plain']
    formatter.for_type(str, str_formatter)
    formatter.for_type(int, int_formatter)
    formatter.for_type(sympy.Integer, int_formatter)
    formatter.for_type(complex, complex_formatter)
    formatter.for_type(datetime.datetime, datetime_formatter)
    formatter.for_type(datetime.timedelta, timedelta_formatter)
    formatter.for_type(sympy.Expr, sympy_expr_formatter)
    formatter.for_type(sympy.matrices.common.MatrixCommon, sympy_expr_formatter)
    formatter.for_type(list, sympy_iterable_formatter)
    formatter.for_type(tuple, sympy_iterable_formatter)
    formatter.for_type(dict, sympy_dict_formatter)
    formatter.for_type(sympy.core.function.FunctionClass, IPython.lib.pretty._function_pprint)

    # use IPython's float precision
    from sympy.printing.pretty.pretty import PrettyPrinter
    from sympy.printing.pretty.stringpict import prettyForm

    def print_float(self, e):
        ipython = IPython.get_ipython()
        form = ipython.display_formatter.formatters['text/plain']
        return prettyForm(form.float_format % e)

    PrettyPrinter._print_Float = print_float
    PrettyPrinter._print_float = print_float

    # for sympy.Integer to support all int's format specifiers:
    def integer__format__(self, format_spec):
        return int.__format__(int(self), format_spec)
    sympy.Integer.__format__ = integer__format__

