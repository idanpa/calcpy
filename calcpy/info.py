from functools import partial
import IPython
import shutil
import sympy
from contextlib import suppress

def print_info_job(res):
    terminal_size = shutil.get_terminal_size()
    page = terminal_size.columns * terminal_size.lines
    pretty = partial(sympy.printing.pretty, num_columns=terminal_size.columns)

    try:
        res_p = pretty(res)
        print(res_p)

        if isinstance(res, (float, sympy.core.numbers.Float)):
            print(f'\n{pretty(sympy.Rational(res))} = Rational(_)')
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
            print(f'\n{pretty(f_expr)}       {pretty(f_dict)} = _.factorint()')
        elif isinstance(res, sympy.Expr):
            # sympy.factor(res, extension=[i]) could be nice (when len(res.free_symbols) >= 1) but not working most of the time
            if len(res.free_symbols) == 1:
                sym = list(res.free_symbols)[0]
                print(f'\n{pretty(sympy.diff(res))} = diff(_)')
                integral = sympy.integrate(res)
                if not isinstance(integral, sympy.integrals.integrals.Integral):
                    print(f'\n{pretty(integral)} = integrate(_)')
                period = sympy.periodicity(res, sym)
                if period is not None:
                    print(f'\n{pretty(period)} = periodicity(_, {sym})')

                # w = sympy.symbols('w')
                # inverse = sympy.solve(sympy.Eq(res.subs(sym, w), sym),w)

            elif len(res.free_symbols) > 1:
                for sym in res.free_symbols:
                    print(f'\n{pretty(sympy.diff(res, sym))} = diff(_, {sym})')
                for sym in res.free_symbols:
                    print(f'\n{pretty(sympy.integrate(res, sym))} = integrate(_, {sym})')
                for sym in res.free_symbols:
                    period = sympy.periodicity(res, sym)
                    if period is not None:
                        print(f'\n{pretty(period)} = periodicity(_, {sym})')

            if res.is_polynomial():
                factored = sympy.polys.polytools.factor(res, gaussian=True)
                if factored != res:
                    print(f'\n{pretty(factored)} = factor(_, gaussian=True)')
            elif len(res.free_symbols) == 1:
                print(f'\n{pretty(sympy.series(res))} = series(_)')

            # takes forever sometimes
            # try:
            #     for sym in res.free_symbols:
            #         print(f'\n{pretty(sympy.calculus.util.minimum(res, sym))} = calculus.util.minimum(_, {sym})')
            #         print(f'{pretty(sympy.calculus.util.maximum(res, sym))} = calculus.util.maximum(_, {sym})')
            # except:
            #     pass

            # takes forever sometimes
            # try:
            #     for sym in res.free_symbols:
            #         print(f'\n{pretty(sympy.calculus.util.continuous_domain(res, sym, sympy.S.Reals))} = calculus.util.continuous_domain(_, {sym}, S.Reals)')
            #         print(f'{pretty(sympy.calculus.util.function_range(res, sym, sympy.S.Reals))} = calculus.util.function_range(_, {sym}, S.Reals)')
            # except:
            #     pass

            if len(res.free_symbols) > 0:
                solutions = sympy.solve(res)
                solutions_print = pretty(solutions)
                if len(solutions_print) > page:
                    solutions_print = pretty(list(map(sympy.N, solutions)))
                print(f'\n{solutions_print} = solve(_)')

            simple = sympy.simplify(res)
            if simple != res:
                print(f'\n{pretty(simple)} = simplify(_)')

            with suppress(NotImplementedError):
                apart = sympy.apart(res)
                if apart != res:
                    print(f'\n{pretty(apart)} = apart(_)')

            trigsimp = sympy.trigsimp(res)
            if trigsimp != res:
                print(f'\n{pretty(trigsimp)} = trigsimp(_)')

            expand_trig = sympy.expand_trig(res)
            if expand_trig != res:
                print(f'\n{pretty(expand_trig)} = expand_trig(_)')

            expand = sympy.expand(res)
            if expand != res:
                print(f'\n{pretty(expand)} = expand(_)')

            doit = res.doit()
            if doit != res:
                print(f'\n{pretty(doit)} = _.doit()')

            N_p = pretty(sympy.N(res))
            if N_p != res_p:
                print(f'\n{N_p} = N(_)')
        elif isinstance(res, sympy.matrices.common.MatrixCommon):
            if res.rows == res.cols:
                print(f'\n{pretty(sympy.det(res))} = det(_)')
                print(f'{pretty(sympy.trace(res))} = trace(_)')
                try:
                    print(f'\n{pretty(res**-1)} = _**-1')
                except:
                    pass
                print(f'\n{pretty(res.charpoly().as_expr())} = _.charpoly().as_expr()')
                evs = res.eigenvects()
                evs_print = pretty(evs)
                if len(evs_print) > page:
                    evs = [(sympy.N(ev[0]), ev[1], tuple(map(sympy.N, ev[2]))) for ev in evs]
                    evs_print = pretty(evs)
                print(f'\n{evs_print} = _.eigenvects() # ((eval, mult, evec),...')
                with suppress(sympy.matrices.matrices.MatrixError):
                    diag = res.diagonalize()
                    diag_print = pretty(diag)
                    if len(diag_print) > page:
                        diag_print = pretty(list(map(sympy.N, diag)))
                    print(f'\n{diag_print} = _.diagonalize() # (P,D) so _=PDP^-1')
            elif res.rows > 1 and res.cols > 1:
                print(f'\n{pretty(res.rank())} = _.rank()')
                print(f'\n{pretty(res.pinv())} = _.pinv()')
            else: # vector
                norm = res.norm()
                print(f'\n{pretty(norm)} = _.norm()')
                print(f'\n{pretty(res/norm)} = _/_.norm()')
        elif isinstance(res, (list, tuple)):
            pass
        elif res is not None:
            try:
                res = sympy.sympify(res)
                print_info_job(res)
            except sympy.SympifyError:
                pass

    except Exception as e:
        print(repr(e))
        return e
    return res

def print_info(res):
    ip = IPython.get_ipython()
    ip.calcpy.jobs.new(print_info_job, res, daemon=True)

def init(ip:IPython.InteractiveShell):
    pass
