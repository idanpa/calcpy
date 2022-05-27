from functools import partial
import IPython
import shutil
import sympy

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

def post_run_cell(result:IPython.core.interactiveshell.ExecutionResult, ip):
    if ip.calcpy.info_asked and result.success and result.result is not None:
        ip.calcpy.jobs.new(print_more_info, result.result, daemon=True)

def init(ip:IPython.InteractiveShell):
    ip.events.register('post_run_cell', partial(post_run_cell, ip=ip))
    ip.calcpy.info_asked = False
