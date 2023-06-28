import ast
import re
import warnings
from functools import partial
import IPython
import sympy
import sympy.interactive.session

# Auxilary classes for manipulations
class UnitPrefix():
    is_unit_prefix = True
class IntegerUnitPrefix(sympy.Integer, UnitPrefix):
    pass
class PowUnitPrefix(sympy.Pow, UnitPrefix):
    pass
class MulUnitPrefix(sympy.Mul, UnitPrefix):
    pass

def dateparse(datetime_string):
    import dateparser
    d = dateparser.parse(datetime_string)
    if d is None:
        raise ValueError(f'Could not parse "{datetime_string}" to datetime')
    return d

def is_auto_symbol(var_name):
    return re.fullmatch(r'[^\d\W](_?\d+)?', var_name) is not None

def calcpy_input_transformer_post(lines):
    ip = IPython.get_ipython()
    var_p = r'[^\d\W]\w*' # match any valid variable name

    def re_sub_mult_replace(match, vars):
        # check var is not none, vae not e (since 2e-4 is ambiguous) and this is not a format specifier/middle of name
        if match[3] is None or \
           match[3].lower() == 'e' or \
           match[1] is not None:
            return match[0]
        if match[3] in vars:
            if getattr(vars[match[3]], 'is_unit_prefix', False):
                return f'({match[2]}*{match[3]})'
            else:
                return f'{match[2]}*{match[3]}'
        if is_auto_symbol(match[3]):
            return f'{match[2]}*{match[3]}'

        return match[0]

    user_vars = ip.ev("locals()")

    user_code = ''.join(lines)

    user_code = user_code.replace('⋅','*')
    user_code = user_code.replace('ⅈ','i') # for implicit multiply to detect it

    # make sure we consider newly introduced variables:
    var_def_pattern = r'^({var_p})\s*=(.*)'
    for vars_match in re.finditer(var_def_pattern, user_code, re.MULTILINE):
        user_vars.setdefault(vars_match[1], None)

    code_string_pattern = r'(d?)("(?:\\"|[^"])*"|\'(?:\\\'|[^\'])*\')'
    code_string_matches = list(re.finditer(code_string_pattern, user_code))
    for m in code_string_matches:
        user_code = user_code.replace(m.group(), f'({hash(m.group())})')

    latex_pattern = r'(\$[^$]*\$)'
    if ip.calcpy.parse_latex:
        latex_matches = re.findall(latex_pattern, user_code)
    else:
        latex_matches = []
    latex_matches = set(latex_matches)
    # avoid processing of latex
    for match in latex_matches:
        user_code = user_code.replace(match, f'({hash(match)})')

    # need to be here so we won't replace caret on latex
    if ip.calcpy.caret_power:
        user_code = user_code.replace('^','**')

    if ip.calcpy.auto_permutation:
        def cycle_replace(match):
            return "sympy.combinatorics.Permutation(" + \
                match[0].strip('()').replace(' ',',') + ")"
        cycle_pat = r'\((\d+ )+\d+\)'
        user_code = re.sub(cycle_pat, cycle_replace, user_code)

    if ip.calcpy.implicit_multiply: # asterisk-free multiplication: 4MB => 4*MB
        # pattern is (format string detection|middle of name detection)?(hex number | engineering number | number)(var name)?
        mult_pat = rf'(% *|[^\d\W])?(0x[0-9a-f]*|0X[0-9A-F]*|\d*\.?\d+e-?\d+|\d*\.?\d+)({var_p})?'
        user_code = re.sub(mult_pat, partial(re_sub_mult_replace, vars=user_vars), user_code)

        # pattern is (right parentheses)(hex number | engineering number | number | var name)
        mult_pat = rf'(\))(0x[0-9a-f]*|0X[0-9A-F]*|\d*\.?\d+e-?\d+|\d*\.?\d+|{var_p})'
        user_code = re.sub(mult_pat, r'\1*\2', user_code)

    for match in latex_matches:
        user_code = user_code.replace(f'({hash(match)})', f'parse_latex(r"""{match[1:-1]}""").subs({{symbols("i"):i}})')

    for m in code_string_matches:
        if ip.calcpy.auto_date and m.group(1) == 'd':
            user_code = user_code.replace(f'({hash(m.group())})', 'dateparse(' + m.group(2) + ')')
        else:
            user_code = user_code.replace(f'({hash(m.group())})', m.group())

    if ip.calcpy.auto_lambda:
        lambda_pattern = rf'^({var_p})\(((?:{var_p}\s*,?\s*)*)\)\s*:=([^=].*)'
        lambda_replace = r'\1= lambda \2 : \3'
        user_code = re.sub(lambda_pattern, lambda_replace, user_code)

    return user_code.splitlines(keepends=True)

class ReplaceIntegerDivisionWithRational(ast.NodeTransformer):
    def __init__(self, ip):
        super().__init__()
        self.ip = ip

    def visit_BinOp(self, node):
        def is_integer(x):
            if isinstance(x, ast.Num) and isinstance(x.n, int):
                return True
            if isinstance(x, ast.Name) and isinstance(self.ip.user_ns.get(x.id, None), int):
                return True
            if isinstance(x, ast.UnaryOp) and isinstance(x.op, (ast.USub, ast.UAdd)):
                return is_integer(x.operand)
            if isinstance(x, ast.BinOp) and isinstance(x.op, (ast.Add, ast.Sub, ast.Mult, ast.Pow)):
                return is_integer(x.left) and is_integer(x.right)
            return False

        if (isinstance(node.op, ast.Div) and is_integer(node.left) and is_integer(node.right)):
            return ast.Call(func=ast.Name(id='Rational', ctx=ast.Load()),
                            args=[node.left, node.right], keywords=[])
        return self.generic_visit(node)

'''
class ReplaceIntWithInteger(ast.NodeTransformer):
    def visit_Constant(self, node):
        if isinstance(node, ast.Num) and isinstance(node.n, int):
            return ast.Call(func=ast.Name(id='Integer', ctx=ast.Load()),
                            args=[node], keywords=[])
        return self.generic_visit(node)
'''

class ReplaceFloatWithRational(ast.NodeTransformer):
    def visit_Constant(self, node):
        if isinstance(node, ast.Num) and isinstance(node.n, float):
            return ast.Call(func=ast.Name(id='Rational', ctx=ast.Load()),
                            args=[ast.Call(func=ast.Name(id='str', ctx=ast.Load()),
                                           args=[node], keywords=[])],
                            keywords=[])
        return self.generic_visit(node)

class ReplaceTupleWithMatrices(ast.NodeTransformer):
    def visit_Tuple(self, node):
        ip = IPython.get_ipython()
        # skip empty tuples and non-nested tuples (e.g some functions uses tuples to represent ranges)
        if not ip.calcpy.auto_matrix or \
           len(node.elts) == 0 or \
           not all(isinstance(el, ast.Tuple) for el in node.elts):
            return self.generic_visit(node)

        matrix_ast = ast.Call(func=ast.Name(id='Matrix', ctx=ast.Load()), args=[node], keywords=[])
        matrix_code = compile(ast.fix_missing_locations(ast.Expression(matrix_ast)), '<string>', 'eval')

        try:
            # sympy would warn if there is a non expression object, use this warning to fallback:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                matrix = ip.ev(matrix_code)
        except:
            return self.generic_visit(node)

        return matrix_ast

class AutoSymbols(ast.NodeTransformer):
    def visit_Name(self, node):
        ip = IPython.get_ipython()
        if ip.calcpy.auto_symbols and node.id not in ip.user_ns and is_auto_symbol(node.id):
            ip.calcpy.push({node.id: sympy.symbols(node.id)}, interactive=False)
        return self.generic_visit(node)

def syntax_error_handler(ip: IPython.InteractiveShell, etype, value, tb, tb_offset=None):
    if ip.calcpy.auto_solve and \
       etype is SyntaxError and tb.tb_next and not tb.tb_next.tb_next:
        if 'cannot assign to ' in str(value):
            try:
                code = ip.user_ns['In'][-1]
            except (KeyError, IndexError):
                pass
            else:
                code = re.sub(r'(.*[^=])=([^=].*)', r'solve(Eq(\1, \2))', code)
                ip.run_cell(code, store_history=False)
                return None
    ip.showsyntaxerror()
    return None

def init(ip: IPython.InteractiveShell):
    # python might warn about the syntax hacks (on user's code)
    warnings.filterwarnings("ignore", category=SyntaxWarning)

    ip.ast_transformers.append(ReplaceIntegerDivisionWithRational(ip))
    # ip.ast_transformers.append(ReplaceIntWithInteger())
    ip.ast_transformers.append(ReplaceFloatWithRational())
    ip.ast_transformers.append(ReplaceTupleWithMatrices())
    ip.ast_transformers.append(AutoSymbols())
    ip.input_transformers_post.append(calcpy_input_transformer_post)

    ip.set_custom_exc((SyntaxError,), syntax_error_handler)

    def sympy_expr_call(self, *args):
        if len(args) != 1:
            raise ValueError('Implicit multiply of sympy expression expects a single argument')
        return self.__rmul__(args[0])

    def sympy_expr_getitem(self, args):
        if not isinstance(args, tuple):
            args = (args,)
        sorted_symbols = sorted(self.free_symbols, key=lambda s: s.name)
        if len(args) != len(sorted_symbols):
            raise TypeError(f'Expected {len(sorted_symbols)} arguments {sorted_symbols}')
        return self.subs(zip(sorted_symbols, args))

    # monkey patches
    sympy.Expr.__call__ = sympy_expr_call
    sympy.Expr.__getitem__ = sympy_expr_getitem
    # don't consider expressions as iterables: (see iterable() in sympy\utilities\iterables.py)
    sympy.Expr._iterable = False
    sympy.Expr.real = property(sympy.re)
    sympy.Expr.imag = property(sympy.im)

