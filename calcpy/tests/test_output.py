#!/usr/bin/env python3
import os
from time import sleep

OUTPUT_FILE_PATH = os.path.join(os.path.dirname(__file__), 'output.txt')

def run_flow(ip):
    def run_cell(raw_cell):
        print('In [0]: ' + raw_cell)
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
        assert captured.out == f.read(), \
            r'output mismatch, regenerate output by `python calcpy\tests\test_output.py`'
        assert captured.err == ''

class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)

    def flush(self):
        for s in self.streams:
            s.flush()

if __name__ == '__main__':
    import sys
    from IPython.testing.globalipapp import start_ipython

    ip = start_ipython()
    print(f'profile: {ip.profile_dir.location}')
    ip.run_line_magic('load_ext', 'calcpy')
    print(f'writing output to {OUTPUT_FILE_PATH}')
    f = open(OUTPUT_FILE_PATH, 'w', encoding='utf-8')
    sys.stdout = Tee(sys.stdout, f)
    run_flow(ip)

