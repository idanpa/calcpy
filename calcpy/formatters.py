import IPython
import sympy
import datetime

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
    pretty_s = sympy.printing.pretty(s)
    printer.text(f'{pretty_s}')
    if not isinstance(s, (sympy.core.numbers.Integer, sympy.core.numbers.Float)):
        evaluated_s = sympy.printing.pretty(sympy.N(s))
        if pretty_s != evaluated_s:
            printer.text(f' ≈ {evaluated_s}')

def init(ip):
    formatter = ip.display_formatter.formatters['text/plain']
    formatter.for_type(str, str_formatter)
    formatter.for_type(int, int_formatter)
    formatter.for_type(complex, complex_formatter)
    formatter.for_type(datetime.datetime, datetime_formatter)
    formatter.for_type(sympy.Expr, sympy_expr_formatter)
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