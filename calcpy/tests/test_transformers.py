from sympy import symbols
from datetime import datetime

def test_autodate(ip):
    dt = ip.run_cell('d"today"-d"yesterday"').result
    assert dt.days == 1 or 24*60*60-1 <= dt.seconds <= 24*60*60
    assert ip.run_cell('d\'1 January 1970\'').result == datetime(1970, 1, 1)

def test_auto_product(ip):
    assert ip.run_cell('2(1+1)').result == 4
    assert ip.run_cell('(1+1)2').result == 4
    assert ip.run_cell('(1+1)0x10').result == 0x20
    assert ip.run_cell('(1+1)2e2').result == 400
    ip.run_cell('var = 3')
    assert ip.run_cell('2var').result == 6
    assert ip.run_cell('0x10var').result == 0x30
    assert ip.run_cell('2e2var').result == 600
    x = ip.run_cell('x').result
    y = ip.run_cell('y').result
    assert ip.run_cell('x(x+1)').result == x*(x+1)
    assert ip.run_cell('(x+1)x').result == (x+1)*x
    assert ip.run_cell('2(x+1)').result == 2*(x+1)
    assert ip.run_cell('(x+1)2').result == (x+1)*2
    assert ip.run_cell('5x^5 + 4x ^ 4 + 3x**3 + 2x ** 2').result == 5*x**5 + 4*x**4 + 3*x**3 + 2*x**2
    assert ip.run_cell('5x^y').result == 5*x**y
    assert ip.run_cell('f\'{1.1:1.2f}\'').result == '1.10'
    assert ip.run_cell('\'%1.2f\' % 1.234').result == '1.23'

def test_caret_power(ip):
    ip.calcpy.caret_power = True
    assert ip.run_cell('3^3').result == 27

def test_auto_lambda(ip):
    ip.run_cell('f(x,y):=x+y')
    assert ip.run_cell('f(1,2)').result == 3

def test_auto_matrix(ip):
    assert ip.run_cell('((1,0),(0,1)).det()').result == 1

def test_auto_latex(ip):
    assert ip.run_cell('$\\frac{1}{2}$.evalf()').result == 0.5
    assert ip.run_cell('$1$ + $1$ + $1+1$').result == 4
    assert ip.run_cell('$x+y$ == x+y').result == True
    ip.run_cell('a,b = 3,4')
    assert ip.run_cell('$a+b$').result == 7
    ip.calcpy.auto_latex_sub = False
    assert ip.run_cell('$a+b$').result == symbols('a') + symbols('b')

def test_auto_symbols(ip):
    assert ip.run_cell('x+y_1+z2').result == symbols('x')+symbols('y_1')+symbols('z2')

def test_auto_factorial(ip):
    assert ip.run_cell('5!').result == 120
    assert ip.run_cell('5!+1').result == 121
    assert ip.run_cell('5!=6').result == True

def test_f_string(ip):
    assert ip.run_cell("f'{2x} {{2x}} {2^2}'").result == '2*x {2x} 4'
