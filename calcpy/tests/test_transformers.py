from sympy import symbols, I
from datetime import datetime

def test_auto_date(ip):
    dt = ip.run_cell('d"today"-d"yesterday"').result
    assert dt.days == 1 or 24*60*60-1 <= dt.seconds <= 24*60*60
    assert ip.run_cell('d\'1 January 1970\'').result == datetime(1970, 1, 1)

def test_auto_symbols(ip):
    assert ip.run_cell('x+y_1+z2').result == symbols('x')+symbols('y_1')+symbols('z2')

    assert ip.run_cell('x').result == symbols('x')
    ip.run_cell('symbols("x", real=True)')
    assert ip.run_cell('x.is_real').result == True
    ip.run_cell('del x')
    assert ip.run_cell('x.is_real').result == None

    ip.run_cell('symbols("x", real=True)')
    ip.run_cell('f = x**2 + 1')
    assert ip.run_cell('solve(x**2 + 1)').result == []
    ip.run_cell('symbols("x", complex=True, real=None)')
    assert ip.run_cell('solve(f)').result == [-I, I]

    # fixme:
    # ip.run_cell('f = $a + b + c$')
    # assert ip.run_cell('f.is_integer').result == None
    # ip.run_cell('symbols("a b c", integer=True)')
    # assert ip.run_cell('f.is_integer').result == True

    ip.run_cell('symbols("y", real=True)')
    assert ip.run_cell('y.is_real').result == True

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
    assert ip.run_cell('(x+1)2y').result == (x+1)*2*y
    assert ip.run_cell('5x^5 + 4x ^ 4 + 3x**3 + 2x ** 2').result == 5*x**5 + 4*x**4 + 3*x**3 + 2*x**2
    assert ip.run_cell('5x^y').result == 5*x**y
    assert ip.run_cell('1/2x').result == x/2 # controversial

    assert ip.run_cell('f\'{1.1:1.2f}\'').result == '1.10'
    assert ip.run_cell('\'%1.2f\' % 1.234').result == '1.23'
    assert ip.run_cell('\'%.3f\' % 1.234').result == '1.234'

    assert ip.run_cell('10MB/1MB').result == 10

    # check no false positives:
    assert ip.run_cell('0b1010').result == 0b1010
    assert ip.run_cell('0x10f').result == 0x10f

def test_unicode_pow(ip):
    x = ip.run_cell('x').result
    assert ip.run_cell('x⁻¹³⁴').result == x**-134

def test_caret_power(ip):
    ip.calcpy.caret_power = True
    assert ip.run_cell('3^3').result == 27

def test_lr_quotation_marks(ip):
    assert ip.run_cell('“string”').result == 'string'

def test_auto_lambda(ip):
    ip.run_cell('f(x,y):=x+y')
    assert ip.run_cell('f(1,2)').result == 3

def test_auto_matrix(ip):
    assert ip.run_cell('((1,0),(0,1)).det()').result == 1

def test_auto_latex(ip):
    assert ip.run_cell('$\\frac{1}{2}$.evalf()').result == 0.5
    assert ip.run_cell('$1$ + $1$ + $1+1$').result == 4
    assert ip.run_cell('f = x+y')
    assert ip.run_cell('$x+y$ == f').result == True
    ip.run_cell('a,b = 3,4')
    assert ip.run_cell('$a+b$').result == 7
    assert ip.run_cell('$i$').result == I
    ip.calcpy.auto_latex_sub = False
    assert ip.run_cell('$a+b$').result == symbols('a') + symbols('b')
    assert ip.run_cell('$i$').result == I

def test_auto_factorial(ip):
    assert ip.run_cell('5!').result == 120
    assert ip.run_cell('5!+1').result == 121
    assert ip.run_cell('5!=6').result == True

def test_string_handling(ip):
    assert ip.run_cell('"2x"').result == '2x'
    assert ip.run_cell('\'2x\'').result == '2x'
    assert ip.run_cell('"""2x"""').result == '2x'
    assert ip.run_cell('\'\'\'2x\'\'\'').result == '2x'
    assert ip.run_cell('"2x \\"2x\\" 2x"').result == '2x "2x" 2x'
    assert ip.run_cell('"2x \\\'2x\\\' 2x"').result == '2x \'2x\' 2x'
    assert ip.run_cell("f'{2x} {{2x}} {2^2}'").result == '2*x {2x} 4'

def test_unicode_power(ip):
    assert ip.run_cell('x³').result == symbols('x') ** 3
    assert ip.run_cell('x⁻¹').result == symbols('x') ** -1

def test_auto_solve(ip):
    assert ip.run_cell('x^2+2=11').result == [-3, 3]
