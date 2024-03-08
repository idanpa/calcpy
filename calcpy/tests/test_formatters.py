from sympy.abc import x, y
from sympy import I as i
from sympy import Rational
from IPython.lib.pretty import pretty
from calcpy.formatters import evalf

def test_unicode_power(ip):
    assert pretty(x**3+2*x**2+3) == 'x³ + 2⋅x² + 3'
    assert pretty(x**-1) == 'x⁻¹'
    assert pretty((x+y)**-1) == '(x + y)⁻¹'
    assert pretty((x+y/5)**-2) == '(x + y/5)**(-2)'
    assert pretty((x/y)**-2) == 'y**2/x**2'

def test_evalf(ip):
    assert evalf(x**2+2*x+1) == (x+1)**2
    assert evalf((x+1)**2) == x**2+2*x+1
    assert evalf((i+1)*(i-1)) == -2
    assert evalf((i+1)/(i-1)) == -i
    assert evalf(Rational(1,2)) == 0.5
