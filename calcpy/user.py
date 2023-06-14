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
Im = im                 # just to be consistent
Re.__name__ = 'Re'
Im.__name__ = 'Im'
import re
from sympy.stats import *
from sympy.plotting import plot3d

# aliases:
choose = binomial
π = pi
i = I
j = I

import datetime

from calcpy.info import print_info

# units manipulation:
class UnitPrefix():
    is_unit_prefix = True
class IntegerUnitPrefix(Integer, UnitPrefix):
    pass
class PowUnitPrefix(Pow, UnitPrefix):
    pass
class MulUnitPrefix(Mul, UnitPrefix):
    pass

G = IntegerUnitPrefix(1e9)
M = IntegerUnitPrefix(1e6)
k = IntegerUnitPrefix(1e3)
m = PowUnitPrefix(10, -3)
u = PowUnitPrefix(10, -6)
n = PowUnitPrefix(10, -9)
p = PowUnitPrefix(10, -12)

KB = IntegerUnitPrefix(2**10)
MB = IntegerUnitPrefix(2**20)
GB = IntegerUnitPrefix(2**30)
TB = IntegerUnitPrefix(2**40)

deg = MulUnitPrefix(Rational(1, 180), pi)

# variables:
x, y, t = symbols('x y t', real=True)
z = symbols('z', complex=True)
m, n, l = symbols('m n l', integer=True)
a, b, c, d = symbols('a b c d', real=True)

# user functions:
from calcpy.transformers import dateparse
from calcpy.formatters import bin2int
from calcpy.utils import copy
from calcpy import get_calcpy

def edit_user_startup():
    get_calcpy().edit_user_startup()

def popcount(x):
    return bin(x).count('1')

def ctz(x):
    return len(bin(x)) - len(bin(x).rstrip('0'))
