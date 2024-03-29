# Content of this file is pushed into user's context:
try:
    import numpy as np
except (ModuleNotFoundError, ImportError):
    pass
try:
    import matplotlib
    import matplotlib.pyplot as plt
except (ModuleNotFoundError, ImportError):
    pass

import IPython
import sympy
from sympy import *
from sympy.combinatorics import *
e = E                   # avoid conflict with sympy.stats expectation
Re = re                 # avoid conflict with python re
Im = im                 # just to be consistent
Re.__name__ = 'Re'
Im.__name__ = 'Im'
import re
from sympy.stats import *
from sympy.plotting import plot3d, plot_contour, plot3d_parametric_surface, plot3d_parametric_line

del beta, gamma, Beta, Gamma # avoid conflict with auto variables

# aliases:
choose = binomial
π = pi
i = I
j = I

import datetime

from calcpy.info import print_info
from calcpy.transformers import IntegerUnitPrefix, PowUnitPrefix, MulUnitPrefix

KB = IntegerUnitPrefix(2**10)
MB = IntegerUnitPrefix(2**20)
GB = IntegerUnitPrefix(2**30)
TB = IntegerUnitPrefix(2**40)

deg = MulUnitPrefix(Rational(1, 180), pi)

# user functions:
from calcpy.transformers import dateparse, parse_latex
from calcpy.formatters import bin2int
from calcpy.utils import copy
from calcpy import get_calcpy

def edit_user_startup():
    get_calcpy().edit_user_startup()

def popcount(x):
    return bin(x).count('1')

def ctz(x):
    return len(bin(x)) - len(bin(x).rstrip('0'))
