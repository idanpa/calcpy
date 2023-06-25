from calcpy.transformers import IntegerUnitPrefix, PowUnitPrefix

G = IntegerUnitPrefix(1e9)
M = IntegerUnitPrefix(1e6)
k = IntegerUnitPrefix(1e3)
m = PowUnitPrefix(10, -3)
u = PowUnitPrefix(10, -6)
n = PowUnitPrefix(10, -9)
p = PowUnitPrefix(10, -12)
