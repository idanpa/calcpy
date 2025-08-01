from functools import partial
import IPython
from IPython.core import inputtransformer2
import shutil
import sympy
from contextlib import suppress
from time import sleep
import re

def print_info_job(res):
    ip = IPython.get_ipython()
    terminal_size = shutil.get_terminal_size()
    page = terminal_size.columns * terminal_size.lines
    pretty = partial(sympy.printing.pretty, num_columns=terminal_size.columns)

    sleep(0.05) # so prints won't clash

    try:
        res_p = pretty(res)

        if isinstance(res, (float, sympy.Float)):
            print(f'\n{pretty(sympy.Rational(res))} = Rational(_)')
        elif isinstance(res, (complex, sympy.Rational)):
            pass
        elif isinstance(res, (int, sympy.Integer)):
            factors_dict = sympy.factorint(res)
            factors_expr = sympy.Mul(*[sympy.Pow(base, expo, evaluate=False) for base, expo in factors_dict.items()], evaluate=False)
            print(f'\n{pretty(factors_expr)}       {pretty(factors_dict)} = factorint(_)')
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
                with suppress(sympy.PoleError):
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
        elif isinstance(res, sympy.matrices.MatrixBase):
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
                try:
                    diag = res.diagonalize()
                    diag_print = pretty(diag)
                    if len(diag_print) > page:
                        diag_print = pretty(list(map(sympy.N, diag)))
                    print(f'\n{diag_print} = _.diagonalize() # (P,D) so _=PDP^-1')
                except sympy.matrices.matrices.MatrixError:
                    jord = res.jordan_form(chop=ip.calcpy.chop)
                    jord_print = pretty(jord)
                    if len(jord_print) > page:
                        jord_print = pretty(list(map(sympy.N, jord)))
                    print(f'\n{jord_print} = _.jordan_form() # (P,J) so _=PJP^-1')

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

def print_info(res):
    ip = IPython.get_ipython()
    ip.calcpy.jobs.new(print_info_job, res, daemon=True)

def init(ip:IPython.InteractiveShell):
    inputtransformer2._help_end_re = re.compile(r"""([^?]*)()(\?\??)$""")

    old_make_help_call = inputtransformer2._make_help_call

    def calcpy_info_make_help_call(target, esc):
        return f'''
if isinstance({target}, (float, sympy.Float, complex, sympy.Rational, int, sympy.Integer, sympy.Expr,
                  sympy.integrals.integrals.Integral, sympy.matrices.MatrixBase)):
    print_info({target})
else:
    {old_make_help_call(target, esc)}
{target}
'''

    inputtransformer2._make_help_call = calcpy_info_make_help_call
