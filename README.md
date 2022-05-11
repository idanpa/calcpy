# CalcPy 🧮 🐍

Calculator and advanced math solver in the comfort of your terminal, using Python,   
IPython and SymPy with tweeks to make it usable as a calculator.

## Installation 
```
pip install git+https://github.com/idanpa/calcpy
```
requirements: ipython sympy matplotlib   
optional: dateparser antlr-python-runtime numpy
## Usage
Launch a session: 
```
$ calcpy
```
## Features
[Python](https://www.python.org/) features:
* All the basic arithmetic (`+`,`-`,`*`,`/`,`**`)
* Programmer: `0b10` binary input, `0x1F` hexadecimal input, `//` integer division, `%` modulo, `&` bitwise AND, `|` bitwise OR, `^` bitwise XOR, `~` bitwise not, `>>`/`<<` right/left shift. 
* Complex numbers (`j`/`i`)

[IPython](https://ipython.org) features:
* Get last result with `_`, or using cell number `_4` (`Out[4]` works too) 
* `func_name?` show docs for func_name
* `who_ls` see all defined variables
* Prompt history with `up`/`down`, search with `ctrl+r`

[SymPy](https://www.sympy.org) features:
* All the elementary (and non-elementry) math functions - `ln`, `sin` etc. 
* Partial list of usefull functions: `diff`, `integrate`, `limit`, `Sum`, `solve`, `plot`, `plot_implicit`

CalcPy features:
* Everything is imported and ready to use (see [user.py](calcpy/user.py))
* Display both symbolic and numeric solutions
* Integers displayed on hex and binary
* Tuples are matrices `((1,2),(3,4))**2`        
* `?` prefix would provide some basic analysis of expression `?((1,2),(3,4))` `?x**2+1` 
* Implicit multiplication (`2x`, `(x+1)(x-1)` are valid)
* All variables stored and restored between sessions (so you can set your own constants e.g. `speed_of_light = 299792458`)
* Currency conversion `10USD` (`calcpy.base_currency='EUR'` to change base currency)
* Strings automatically converted to datetime `"yesterday at 9 am" - "1990-1-30 9:20"` (using [dateparser](https://github.com/scrapinghub/dateparser))
* Unit prefixes `G`, `M`, `k`, `m`, `u`, `n`, `p`, `KB`, `MB`, `GB`, `TB` (so `4MB-32KB` or `4G/32n` are valid)
* Implicit lambda `f(a,b)=a**2+b**2`
* Latex input `plot($\frac{1,x}$)` (latex output with `latex(1/x)`)

## Warranty
Provided "as is", without warranty of any kind 😊
