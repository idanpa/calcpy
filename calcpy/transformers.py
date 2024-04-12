import ast
import re
import warnings
import IPython
import sympy
import sympy.parsing.latex

# Auxilary classes for manipulations
class UnitPrefix():
    is_unit_prefix = True
class IntegerUnitPrefix(sympy.Integer, UnitPrefix):
    pass
class PowUnitPrefix(sympy.Pow, UnitPrefix):
    pass
class MulUnitPrefix(sympy.Mul, UnitPrefix):
    pass

class FactorialPow():
    # using power so factorial would take the right precedence
    def __rpow__(self, other):
        return sympy.factorial(other)

def dateparse(datetime_string):
    import dateparser
    d = dateparser.parse(datetime_string)
    if d is None:
        raise ValueError(f'Could not parse "{datetime_string}" to datetime')
    return d

def parse_latex(s):
    ip = IPython.get_ipython()
    try:
        # don't take the default assumptions of symbols created by parser:
        sympy.Symbol._ignore_assumptions = True
        expr = sympy.parsing.latex.parse_latex(s)
    finally:
        sympy.Symbol._ignore_assumptions = False
    expr = expr.subs({'i': sympy.I})
    if not ip.calcpy.auto_latex_sub:
        return expr
    for sym in expr.free_symbols.copy():
        if sym.name in ip.user_ns:
            expr = expr.subs(sym, ip.user_ns[sym.name])
        else:
            ip.push({sym.name: sym})
    return expr

def is_auto_symbol(var_name):
    var_name_no_idx = re.sub(r'_?\d+$', '', var_name)
    return re.fullmatch(r'[^\d\W]', var_name_no_idx) is not None or \
        var_name_no_idx in ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 'iota', 'kappa', 'lamda',
                            'mu', 'nu', 'xi', 'omicron', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega']

def calcpy_input_transformer_post(lines):
    return raw_code_transformer(''.join(lines)).splitlines(keepends=True)

def raw_code_transformer(code):
    ip = IPython.get_ipython()
    var_pat = r'[^\d\W]\w*' # match any valid variable name

    user_vars = ip.user_ns.copy()
    # consider also newly introduced variables:
    var_def_pattern = rf'^({var_pat})\s*=(.*)'
    for vars_match in re.finditer(var_def_pattern, code, re.MULTILINE):
        user_vars.setdefault(vars_match[1], None)

    # before doing anything, extract strings and latex, we don't want to transform these:
    code_string_matches = {}
    # (string modifiers)("str"|'str'|"""str"""|'''str''')
    str_pat = r'([bdfr]{0,2})("(?:\\"|[^"])+"|\'(?:\\\'|[^\'])+\'|"""([\S\s]*?)(?<!\\)"""|\'\'\'([\S\s]*?)(?<!\\)\'\'\')'
    for m in re.finditer(str_pat, code):
        key = hash(m.group())
        code = code.replace(m.group(), f'({key})')
        if ip.calcpy.auto_date and m.group(1) == 'd':
            code_string_matches[key] = 'dateparse(' + m.group(2) + ')'
        elif 'f' in m.group(1): # recursive on f-strings
            code_string_matches[key] = re.sub(r'(?<=(?<!{){)[^{}]*(?=}(?!}))', lambda match: raw_code_transformer(match[0]), m.group())
        else:
            code_string_matches[key] = m.group()

    latex_matches = {}
    latex_pattern = r'\$([^$]*)\$'
    if ip.calcpy.auto_latex:
        for m in re.finditer(latex_pattern, code):
            key = hash(m.group())
            code = code.replace(m.group(), f'({key})')
            latex_matches[key] = f'parse_latex(r"""{m[1]}""")'

    code = code.replace('⋅','*')
    code = code.replace('ⅈ','i') # for auto product to detect it
    u2i = {'\u2070':'0','\u00b9':'1','\u00b2':'2','\u00b3':'3','\u2074':'4','\u2075':'5','\u2076':'6','\u2077':'7','\u2078':'8','\u2079':'9'}
    def unicode_pow_replace(match):
        s = '**'
        if match[1]:
            s += '-'
        for c in match[2]:
            s += u2i[c]
        return s
    unicode_pow_pat = f'(\u207b)?(({"|".join(u2i.keys())})+)'
    code = re.sub(unicode_pow_pat, unicode_pow_replace, code)

    if ip.calcpy.caret_power:
        code = re.sub(r'(?<!\^)\^(?!\^)', '**', code)
        code = code.replace('^^','^')

    if ip.calcpy.auto_factorial:
        code = re.sub(r'!(?!=)', r'**_factorial_pow', code)

    if ip.calcpy.auto_permutation:
        def cycle_replace(match):
            return "sympy.combinatorics.Permutation(" + \
                match[0].strip('()').replace(' ',',') + ")"
        cycle_pat = r'\((\d+ )+\d+\)'
        code = re.sub(cycle_pat, cycle_replace, code)

    def auto_prod_replace(match):
        # check var is not none, var not e (since 2e-4 is ambiguous), not a format specifier/middle of name
        if match[3] is None or \
           match[3].lower() == 'e' or \
           match[1] is not None:
            return match[0]
        if match[3] in user_vars:
            if getattr(user_vars[match[3]], 'is_unit_prefix', False):
                return f'({match[2]}*{match[3]})'
            else:
                return f'{match[2]}*{match[3]}'
        if is_auto_symbol(match[3]):
            return f'{match[2]}*{match[3]}'

        return match[0]

    if ip.calcpy.auto_product:
        # number - binary/octal/hex | engineering number | number
        num_pat = r'0[bBoOxX][0-9a-fA-F]*|\d*\.?\d+e-?\d+|\d*\.?\d+'
        # prod - (format spec|middle of name detection)?(number)(var name)?
        prod_pat = rf'(: *|[^\d\W])?({num_pat})({var_pat})?'
        code = re.sub(prod_pat, auto_prod_replace, code)

        # pattern is (right parentheses)(binary/octal/hex | engineering number | number | var name)
        prod_pat = rf'(\))(0[bBoOxX][0-9a-fA-F]*|\d*\.?\d+e-?\d+|\d*\.?\d+|{var_pat})'
        code = re.sub(prod_pat, r'\1*\2', code)

    for key, val in latex_matches.items():
        code = code.replace(f'({key})', val)

    for key, val in code_string_matches.items():
        code = code.replace(f'({key})', val)

    if ip.calcpy.auto_lambda:
        lambda_pattern = rf'^({var_pat})\(((?:{var_pat}\s*,?\s*)*)\)\s*:=([^=].*)'
        lambda_replace = r'\1= lambda \2 : \3'
        code = re.sub(lambda_pattern, lambda_replace, code)

    if ip.calcpy.auto_solve:
        try:
            ip.compile.ast_parse(code)
        except Exception as e:
            if isinstance(e, SyntaxError) and 'cannot assign to ' in str(e):
                code = re.sub(r'(.*[^=])=([^=].*)', r'solve(Eq(\1, \2))', code)

    if ip.calcpy._print_transformed_code:
        print(code)
    return code

class AstNodeTransformer(ast.NodeTransformer):
    def __init__(self, ip):
        super().__init__()
        self.ip = ip

class ReplaceIntegerDivisionWithRational(AstNodeTransformer):
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

        if self.ip.calcpy.auto_rational:
            if (isinstance(node.op, ast.Div) and is_integer(node.left) and is_integer(node.right)):
                return ast.Call(func=ast.Name(id='Rational', ctx=ast.Load()),
                                args=[node.left, node.right], keywords=[])
        return self.generic_visit(node)

'''
class ReplaceIntWithInteger(AstNodeTransformer):
    def visit_Constant(self, node):
        if isinstance(node, ast.Num) and isinstance(node.n, int):
            return ast.Call(func=ast.Name(id='Integer', ctx=ast.Load()),
                            args=[node], keywords=[])
        return self.generic_visit(node)
'''

class ReplaceFloatWithRational(AstNodeTransformer):
    def visit_Constant(self, node):
        if self.ip.calcpy.auto_rational:
            if isinstance(node, ast.Num) and isinstance(node.n, float):
                return ast.Call(func=ast.Name(id='Rational', ctx=ast.Load()),
                                args=[ast.Call(func=ast.Name(id='str', ctx=ast.Load()),
                                            args=[node], keywords=[])],
                                keywords=[])
        return self.generic_visit(node)

class ReplaceTupleWithMatrix(AstNodeTransformer):
    def visit_Tuple(self, node):
        # skip empty tuples and non-nested tuples (e.g some functions uses tuples to represent ranges)
        if not self.ip.calcpy.auto_matrix or \
           len(node.elts) == 0 or \
           not all(isinstance(el, ast.Tuple) for el in node.elts):
            return self.generic_visit(node)

        matrix_ast = ast.Call(func=ast.Name(id='Matrix', ctx=ast.Load()), args=[node], keywords=[])
        matrix_code = compile(ast.fix_missing_locations(ast.Expression(matrix_ast)), '<string>', 'eval')

        try:
            # sympy would warn if there is a non expression object, use this warning to fallback:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                matrix = self.ip.ev(matrix_code)
        except:
            return self.generic_visit(node)

        return matrix_ast

class AutoSymbols(AstNodeTransformer):
    def visit_Name(self, node):
        if self.ip.calcpy.auto_symbols:
            if node.id not in self.ip.user_ns and is_auto_symbol(node.id):
                self.ip.calcpy.push({node.id: sympy.symbols(node.id)}, interactive=False)
        return self.generic_visit(node)

class AutoProduct(AstNodeTransformer):
    def visit_Call(self, node):
        if self.ip.calcpy.auto_product and len(node.args) == 1 and node.keywords==[] and (
           (isinstance(node.func, ast.Name) and isinstance(self.ip.user_ns.get(node.func.id, None), (sympy.Expr, int, float, complex))) or \
           (isinstance(node.func, ast.Constant) and isinstance(node.func.value, (int, float, complex)))):
            return ast.BinOp(left=node.func, op=ast.Mult(), right=node.args[0])
        return self.generic_visit(node)

def init(ip: IPython.InteractiveShell):
    ip.calcpy.push({'_factorial_pow': FactorialPow()}, interactive=False)

    # python might warn about the syntax hacks (on user's code)
    warnings.filterwarnings("ignore", category=SyntaxWarning)

    ip.ast_transformers.append(AutoSymbols(ip))
    ip.ast_transformers.append(ReplaceIntegerDivisionWithRational(ip))
    # ip.ast_transformers.append(ReplaceIntWithInteger(ip))
    ip.ast_transformers.append(ReplaceFloatWithRational(ip))
    ip.ast_transformers.append(ReplaceTupleWithMatrix(ip))
    ip.ast_transformers.append(AutoProduct(ip))
    ip.input_transformers_post.append(calcpy_input_transformer_post)

    # monkey patches
    # don't consider expressions as iterables: (see iterable() in sympy\utilities\iterables.py)
    sympy.Expr._iterable = False
    sympy.Expr.real = property(sympy.re)
    sympy.Expr.imag = property(sympy.im)
    # numpy - sympy interoperability
    try:
        import numpy as np
        def sympy_int_array(self, dtype=np.dtype(int)):
            return np.array(int(self), dtype=dtype)
        def sympy_float_array(self, dtype=np.dtype(float)):
            return np.array(float(self), dtype=dtype)
        sympy.Rational.__array__  = sympy_float_array
        sympy.Float.__array__  = sympy_float_array
        sympy.NumberSymbol.__array__  = sympy_float_array
        sympy.Integer.__array__  = sympy_int_array
    except (ModuleNotFoundError, ImportError):
        pass

    # unified assumptions for symbol name
    sympy.Symbol._all_symbols = {}
    sympy.Symbol._ignore_assumptions = False
    sympy_symbol_xnew = sympy.Symbol.__xnew__
    def unified_sympy_symbol_xnew(cls, name, ignore_assumptions=False, **assumptions):
        new_symbol = sympy_symbol_xnew(cls, name, **assumptions)
        if not ip.calcpy.uniform_assumptions or cls != sympy.Symbol:
            return new_symbol
        if name not in sympy.Symbol._all_symbols:
            sympy.Symbol._all_symbols[name] = new_symbol
        elif not ignore_assumptions and not sympy.Symbol._ignore_assumptions:
            sympy.Symbol._all_symbols[name]._assumptions = new_symbol._assumptions
            sympy.Symbol._all_symbols[name]._assumptions0 = new_symbol._assumptions0
            sympy.Symbol._all_symbols[name]._assumptions_orig = new_symbol._assumptions_orig

        return sympy.Symbol._all_symbols[name]
    sympy.Symbol.__xnew__ = unified_sympy_symbol_xnew
    # disable cache so assumptions could be changed multiple times
    sympy.Symbol._Symbol__xnew_cached_ = unified_sympy_symbol_xnew

