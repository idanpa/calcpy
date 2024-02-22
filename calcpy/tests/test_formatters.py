from sympy.abc import x, y
from IPython.lib.pretty import pretty

def test_unicode_power(ip):
    assert pretty(x**3+2*x**2+3) == 'x³ + 2⋅x² + 3'
    assert pretty(x**-1) == 'x⁻¹'
    assert pretty((x+y)**-1) == '(x + y)⁻¹'
    assert pretty((x+y/5)**-2) == '(x + y/5)**(-2)'
    assert pretty((x/y)**-2) == 'y**2/x**2'
