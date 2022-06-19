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
            # if calcpy.bitwidth
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

def sympy_list_formatter(s, printer, cycle):
    num_columns = shutil.get_terminal_size().columns
    pretty = partial(sympy.printing.pretty, num_columns=num_columns)

    pretty_s = pretty(s)
    out = pretty_s

    try:
        options = {}
        n = 15
        evalu = [el.evalf(n, **options) if hasattr(el, 'evalf') else el for el in s]
        evalu_s = pretty(evalu)
        if evalu_s != pretty_s:
            out = pretty_stack(out, " ≈ ", evalu_s, num_columns)
    except Exception as e:
        if IPython.get_ipython().calcpy.debug:
            print(f'list formatter failed: {e}')

    printer.text(out)

def sympy_expr_formatter(s, printer, cycle):
    num_columns = shutil.get_terminal_size().columns
    pretty = partial(sympy.printing.pretty, num_columns=num_columns)

    pretty_s = pretty(s)
    out = pretty_s

    try:
        if not isinstance(s, (sympy.core.numbers.Integer, sympy.core.numbers.Float)):
            simpl_s = pretty(sympy.simplify(s))
            if simpl_s != pretty_s:
                out = pretty_stack(out, " = ", simpl_s, num_columns)

            doit_s = pretty(s.doit())
            if doit_s != simpl_s and doit_s != pretty_s:
                out = pretty_stack(out, " = ", doit_s, num_columns)

            evalu = sympy.N(s)
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
    formatter.for_type(sympy.Expr, sympy_expr_formatter)
    formatter.for_type(sympy.matrices.common.MatrixCommon, sympy_expr_formatter)
    formatter.for_type(list, sympy_list_formatter)
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

    # # fixing sympy prefixes:
    # def prefix__str__(self):
    #     return str(self.abbrev)
    # sympy.physics.units.prefixes.Prefix.__str__ = prefix__str__
    # sympy.physics.units.prefixes.Prefix.__repr__ = prefix__str__
    # def prefix_evalf(self, prec=None, **options):
    #     return self.scale_factor
    # sympy.physics.units.prefixes.Prefix.evalf = prefix_evalf
    # def evalf_prefix(expr: 'sympy.physics.units.prefixes.Prefix', prec: int, options: sympy.core.evalf.OPT_DICT) -> sympy.core.evalf.TMP_RES:
    #     return sympy.core.evalf.evalf_pow(sympy.Pow(expr.base, expr._exponent, evaluate=False), prec, options)
    # sympy.core.evalf.evalf_table[sympy.physics.units.prefixes.Prefix] = evalf_prefix
