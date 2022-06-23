## Algebra
Matrices:

```
In [1]: ((1,2),(2,4))*((5,6),(7,8))
Out[1]: 
⎡19  22⎤
⎢      ⎥
⎣38  44⎦
```

```
In [1]: a,b,c,d = symbols('a b c d')
In [2]: ((a,b),(c,d))**-1
Out[2]: 
⎡    d         -b    ⎤
⎢─────────  ─────────⎥
⎢a*d - b*c  a*d - b*c⎥
⎢                    ⎥
⎢   -c          a    ⎥
⎢─────────  ─────────⎥
⎣a*d - b*c  a*d - b*c⎦
```

```
In [1]: ((1,2),(2,4))*((x,y),).T
Out[1]: 
⎡ x + 2*y ⎤
⎢         ⎥
⎣2*x + 4*y⎦
```
Detailed information about matrix:
```
In [1]: ?((1,2),(2,3))
```

## Calculus

```
In [1]: diff(sin(x))
Out[1]: cos(x)
```

Detailed information about function:
```
In [1]: ?e**(x**2)
```

This is equivalent to `solve(Eq(8x**2+2x-10,0))`
```
In [1]: 8x**2+2x-10 = 0
Out[1]: [-5/4, 1] ≈ [-1.25, 1]
```

## Plotting
```
In [1]: plot(sin(x))
```
<!-- multiple plots on a single chart (set legend) -->
save the last figure with
```
In [1]: plt.savefig('fig.png')
```

## Programmer
```
In [1]: (34MB - 7000KB)/2MB
Out[1]:  
3477
──── ≈ 13.582
256
```

```
In [1]: (0xab00 >> 8) & 0xff
Out[1]: 171           0xab             1010 1011
```

## Currency

```
In [1]: 400EUR
Out[1]: 428.88⋅USD
In [2]: 100USD
Out[2]: [93.2662⋅EUR  79.1597⋅GBP  669.94⋅CNY  12688.9⋅JPY]
```
base_currency and common_currencies are set automatically.  
Setting different base currency and the common currencies:
```
In [1]: calcpy.base_currency = 'EUR'
In [2]: calcpy.common_currencies = ["USD", "ILS"]
```
## Latex
```
In [1]: $\frac{1}{x}$ * $\sin{x}$
Out[1]: 
sin(x)
──────
  x
In [2]: diff(_)
Out[2]: 
cos(x)   sin(x)
────── - ──────
  x         2
           x
In [3]: latex(_)
Out[3]: \frac{\cos{\left(x \right)}}{x} - \frac{\sin{\left(x \right)}}{x^{2}}
```

## Misc

```
In [1]: sin(60deg)
Out[1]:
√3
──
2  ≈ 0.866025
```

