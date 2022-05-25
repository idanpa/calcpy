import ast
import re
import warnings
from functools import partial
import IPython
import sympy

try:
    import dateparser
    dateparsing = True
except ModuleNotFoundError:
    dateparsing = False

def calcpy_input_transformer_cleanup(lines):
    ip = IPython.get_ipython()
    if (lines[0] != '?\n' and lines[0][0] == '?'):
        ip.calcpy.info_asked = True
        lines[0] = lines[0][1:]
    else:
        ip.calcpy.info_asked = False
    return lines

def calcpy_input_transformer_post(lines):
    ip = IPython.get_ipython()
    var_p = r'[^\d\W]\w*' # match any valid variable name

    def re_sub_mult_replace(match, vars):
        # check var is not none, vae not e (since 2e-4 is ambiguous) and this is not a format specifier
        if match[3] is None or \
           match[3].lower() == 'e' or \
           match[1] is not None:
            return match[0]
        if match[3] in vars:
            return f'({match[2]}*{match[3]})'
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
            # pattern is (format string detection)?(hex number | engineering number | number)(var name)?
            mult_pat = rf'(% ?)?(0x[0-9a-f]*|0X[0-9A-F]*|\d*\.?\d+e-?\d+|\d*\.?\d+)({var_p})?'
            lines[i] = re.sub(mult_pat, partial(re_sub_mult_replace, vars=user_vars), lines[i])

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

class ReplaceStringsWithDates(ast.NodeTransformer):
    def visit_Constant(self, node):
        if isinstance(node, ast.Str):
            ip = IPython.get_ipython()
            if not ip.calcpy.auto_date:
                return self.generic_visit(node)
            dt = dateparser.parse(node.s, settings={'STRICT_PARSING': True})
            if dt:
                return ast.Call(
                    func=ast.Attribute(value=ast.Name(id='datetime', ctx=ast.Load()), attr='datetime', ctx=ast.Load()),
                    args=[ast.Constant(value=dt.year), ast.Constant(value=dt.month), ast.Constant(value=dt.day),
                            ast.Constant(value=dt.hour), ast.Constant(value=dt.minute), ast.Constant(value=dt.second), ast.Constant(value=dt.microsecond)],
                    keywords=[])
        return self.generic_visit(node)


def init(ip):
    ip.ast_transformers.append(ReplaceIntegerDivisionWithRational())
    ip.ast_transformers.append(ReplaceTupleWithMatrices())
    if dateparsing:
        ip.ast_transformers.append(ReplaceStringsWithDates())
    ip.input_transformers_cleanup.append(calcpy_input_transformer_cleanup)
    ip.input_transformers_post.append(calcpy_input_transformer_post)

    def sympy_expr_call(self, *args):
        # single non-constant expression, interpret as product
        if len(args) == 1 and isinstance(args[0], sympy.Expr) and not args[0].is_constant():
                return self.__rmul__(args[0])
        # else, substitute
        sorted_symbols = sorted(self.free_symbols, key=lambda s: s.name)
        if len(args) != len(sorted_symbols):
            raise TypeError(f'Expected {len(sorted_symbols)} arguments {sorted_symbols}')
        return self.subs(zip(sorted_symbols, args))

    sympy.Expr.__call__ = sympy_expr_call
