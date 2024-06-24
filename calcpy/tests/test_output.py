#!/usr/bin/env python3
import os
from time import sleep

OUTPUT_FILE_PATH = os.path.join(os.path.dirname(__file__), 'output.txt')

def run_flow(ip):
    def run_cell(raw_cell):
        print('In [1]: ' + raw_cell)
        ip.run_cell(raw_cell)

    run_cell('12')
    run_cell('30/3deg')
    run_cell('[pi/2, log(x)/sin(y), Sum(1/n**2,(n,1,4))]')
    run_cell('SymmetricGroup(3).conjugacy_classes()')
    run_cell(r'latex(diff($\frac{1}{x}$ * $\sin{x}$))')
    run_cell('8x**2+2x-10 = 0')
    run_cell('23232?')
    sleep(1)
    run_cell('((1,2),(2,3))?')
    sleep(1)
    run_cell('e**(-x**2)?')
    sleep(2)
    run_cell('np.arange(4)')
    run_cell('np.zeros((2,2))')
    run_cell('np.array([[alpha, gamma, x_1]])')

def test_output(ip, capsys):
    run_flow(ip)
    captured = capsys.readouterr()
    with open(OUTPUT_FILE_PATH, 'r', encoding='utf-8') as f:
        assert f.read() == captured.out, \
            r'output mismatch, regenerate output by `python calcpy\tests\test_output.py`'
        assert '' == captured.err

if __name__ == '__main__':
    import os
    from contextlib import redirect_stdout
    from IPython.testing.globalipapp import start_ipython

    ip = start_ipython()
    ip.run_line_magic('load_ext', 'calcpy')
    print(f'writing output to {OUTPUT_FILE_PATH}')
    with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f:
        with redirect_stdout(f):
            run_flow(ip)

