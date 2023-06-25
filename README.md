# CalcPy

Calculator and advanced math solver in the comfort of your terminal by Python, IPython and SymPy.

## Installation 
([Python installation](https://www.python.org/downloads/))
```
pip install git+https://github.com/idanpa/calcpy
```
[Android installation](docs/android.md)
## Usage
```
$ calcpy
```
[Examples](docs/examples.md)  
[Try online](https://replit.com/@idanp/CalcPy?embed=true)

## Features
* Display both symbolic and numeric solutions
* Integers displayed as decimal, hex and binary (control size with `calcpy.bitwidth`)
* Evaluation preview while typing
* Currency conversion `10USD` (`calcpy.base_currency='EUR'` to change base currency)
* `?` prefix would provide some basic analysis of expression (similar to [WolframAlpha](https://www.wolframalpha.com/))  
`?((1,2),(3,4))`, `?x**2+1`, `?234`
* Implicit multiplication (`2x`, `(x+1)(x-1)` are valid)
* Tuples are matrices `((1,2),(3,4))**2`        
* All variables and functions are restored between sessions (delete using `del`)
* Datetime calculations `d"yesterday at 9 am" - d"1990-1-30 9:20"` (using [dateparser](https://github.com/scrapinghub/dateparser))
* Unit prefixes `G`, `M`, `k`, `m`, `u`, `n`, `p`, `KB`, `MB`, `GB`, `TB` (so `4MB-32KB` or `4G/3.2n` are valid)
* Implicit lambda `f(a,b)=a**2+b**2`
* Latex input `plot($\frac{1,x}$)` (latex output with `latex(1/x)`)
* Copy to clipboard `copy(Out[12])`
* Automatic symbols, anything like `x` `y_1` would become sympy symbol
* Custom user startup (for imports, etc.) `edit_user_startup()`
* Persistent configuration, see options with `calcpy?`

[SymPy](https://www.sympy.org):
* All the elementary (and non-elementry) math functions and constants - `ln`, `sin`, `e`, `pi` etc. 
* Calculus, algebra, plotting - `diff`, `integrate`, `limit`, `Sum`, `solve`, `plot`, `plot_implicit` etc.
* Complex numbers `1+2i`

[IPython](https://ipython.org):
* Get last result with `_`, get specific cell `_12` (`Out[12]` works too) 
* `func_name?` show docs for func_name
* `who`/`who_ls` see all defined variables
* Prompt history with `up`/`down`, search with `ctrl+r`
* Autocomplete with `tab`
* Edit code on editor with `%edit func_name`

[Python](https://www.python.org/):
* All the basic arithmetic (`+`,`-`,`*`,`/`,`**`)
* Programmer: `0b10` binary input, `0x1F` hexadecimal input, `//` integer division, `%` modulo, `&` bitwise AND, `|` bitwise OR, `^` bitwise XOR, `~` bitwise not, `>>`/`<<` right/left shift. 

## Contributing
Feel free to open an issue for bugs/features,  send a pull request  or star.
