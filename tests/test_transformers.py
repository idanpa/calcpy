from sympy import symbols

def test_autodate(ip):
    dt = ip.run_cell('d"today"-d"yesterday"').result
    assert dt.days == 1 or 24*60*60-1 <= dt.seconds <= 24*60*60

def test_implicit_multiply(ip):
    ip.run_cell('foo=1')
    assert ip.run_cell('2foo').result == 2

def test_caret_power(ip):
    ip.calcpy.caret_power = True
    assert ip.run_cell('3^3').result == 27

def test_auto_lambda(ip):
    ip.run_cell('f(x,y):=x+y')
    assert ip.run_cell('f(1,2)').result == 3

def test_auto_matrix(ip):
    assert ip.run_cell('((1,0),(0,1)).det()').result == 1

def test_parse_latex(ip):
    assert ip.run_cell('$\\frac{1}{2}$.evalf()').result == 0.5

def test_auto_symbols(ip):
    assert ip.run_cell('x+y_1+z2').result == symbols('x')+symbols('y_1')+symbols('z2')

def test_auto_factorial(ip):
    assert ip.run_cell('5!').result == 120
    assert ip.run_cell('5!+1').result == 121
    assert ip.run_cell('5!=6').result == True
