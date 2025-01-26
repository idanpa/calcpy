<img src="docs/icon.svg" width="70" align="left">

# CalcPy

Terminal programmer calculator and advanced math solver using Python, IPython and SymPy.  
The missing tweaks for using Python as a calculator.

## 🖥 Usage

<p align="left">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/demo/demo_dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="docs/demo/demo_light.svg">
    <img src="docs/demo/demo_light.svg">
  </picture>
</p>

**[🚀 Try online](https://calcpy.duckdns.org)**

## 📦 Installation

```
pip install https://github.com/idanpa/calcpy/archive/main.zip
```
[Android installation](docs/android.md)  

## ✨ Features

* Display both symbolic and numeric solutions
* Integers displayed as decimal, hex and binary
* Evaluation preview while typing
* Currency conversion `10USD` (`calcpy.base_currency='EUR'` to change base currency) (by [ECB](https://www.ecb.europa.eu/))
* `?` suffix provides some basic analysis of expression (similar to [WolframAlpha](https://www.wolframalpha.com/))  
`((1,2),(3,4))?`, `x**2+1?`, `234?`
* Automatic symbolic variables, anything like `x` `y_1` is a sympy symbol
* Symbolic variables assumptions are uniform, `symbols(x, real=True)` would change all occurencase of `x` to be real
* Implicit multiplication (`2x`, `(x+1)(x-1)` are valid)
* Nested tuples are matrices `((1,2),(3,4))**2`        
* All variables and functions are restored between sessions (delete using `del`)
* Datetime calculations `d"yesterday at 9 am" - d"1990-1-30 9:20"` (by [dateparser](https://github.com/scrapinghub/dateparser))
* Sizes `KB`, `MB`, `GB`, `TB` (e.g. `4MB-32KB`)
* Unit prefixes `G`, `M`, `k`, `m`, `u`, `n`, `p` (`4G/3.2n`, enable by `calcpy.units_prefixes=True`)
* Implicit lambda `f(a,b):=a**2+b**2`
* Latex input `diff($\frac{1,x}$)` (latex output with `latex(1/x)`)
* Copy to clipboard `copy(_)` would copy last result
* Custom user startup (for imports, etc.) `edit_user_startup()`
* Persistent configuration, see options with `calcpy?`

#### [SymPy](https://www.sympy.org)

* All the elementary (and non-elementry) math functions and constants - `ln`, `sin`, `e`, `pi` etc. 
* Calculus, algebra, plotting - `diff`, `integrate`, `limit`, `Sum`, `solve`, `plot`, `plot_implicit` etc.

#### [IPython](https://ipython.org)

* Get last result with `_`, get specific cell `_12` (`Out[12]` works too) 
* `func_name?` show docs for func_name
* `who`/`who_ls` see all defined variables
* Prompt history with `up`/`down`, search with `ctrl+r`
* Autocomplete with `tab`
* Edit code on editor with `%edit func_name`

#### [Python](https://www.python.org/)

* All the basic arithmetic `+`,`-`,`*`,`/`,`**` or `^`
* Binary and hex input `0b1101`, `0xafe1`
* Scientific notation `2.12e-6`
* Programmer operations `//` integer division, `%` modulo, `&` bitwise AND, `|` bitwise OR, `^^` bitwise XOR (on calcpy `^` is exponentiation, disable with `calcpy.caret_power`), `~` bitwise not, `>>`/`<<` right/left shift. 

## 🤝 Contributing

Feel free to open an issue for bugs/features,  send a pull request  or star.
