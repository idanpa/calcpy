# Content of this file is pushed into user's context:
try:
    import numpy as np
except ModuleNotFoundError:
    pass
try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    pass
import sympy
from sympy.parsing.latex import parse_latex
from sympy import *
e = E                   # avoid conflict with sympy.stats expectation
Re = re                 # avoid conflict with python re
Im = im
import re
from sympy.stats import *
import datetime

G = 1e9
M = 1e6
k = 1e3
m = 1e-3
u = 1e-6
n = 1e-9
p = 1e-12

KB = 2**10
MB = 2**20
GB = 2**30
TB = 2**40

deg = pi/180

i = I
j = I

x, y, t = symbols('x y t', real=True)
z = symbols('z', complex=True)
m, n, l = symbols('m n l', integer=True)

def popcount(x):
    return bin(x).count('1')

def ctz(x):
    return len(bin(x)) - len(bin(x).rstrip('0'))
