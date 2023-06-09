# CalcPy

Calculator and advanced math solver in the comfort of your terminal by Python, IPython and SymPy.

## Installation 
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
Just an IPython shell with:
* SymPy imported and ready to use  
  `x`,`y`,`t` are real, `z` is complex, `m`,`n`,`l` are integers
* Display both symbolic and numeric solutions
* Integers displayed as decimal, hex and binary (control size with `calcpy.bitwidth`)
* Tuples are matrices `((1,2),(3,4))**2`        
* Result preview while typing
* `?` prefix would provide some basic analysis of expression (similar to [WolframAlpha](https://www.wolframalpha.com/))  
`?((1,2),(3,4))`, `?x**2+1`, `?234`
* Implicit multiplication (`2x`, `(x+1)(x-1)` are valid)
* All variables and functions are restored between sessions (delete using `del`)
* Currency conversion `10USD` (`calcpy.base_currency='EUR'` to change base currency)
<!-- * Strings automatically converted to datetime `"yesterday at 9 am" - "1990-1-30 9:20"` (using [dateparser](https://github.com/scrapinghub/dateparser)) -->
* Unit prefixes `G`, `M`, `k`, `m`, `u`, `n`, `p`, `KB`, `MB`, `GB`, `TB` (so `4MB-32KB` or `4G/32n` are valid)
* Implicit lambda `f(a,b)=a**2+b**2`
* Latex input `plot($\frac{1,x}$)` (latex output with `latex(1/x)`)
* Copy to clipboard `copy(expr)`
* Edit custom user startup (for imports, etc.) `edit_user_startup()`

[SymPy](https://www.sympy.org):
* All the elementary (and non-elementry) math functions and constants - `ln`, `sin`, `e`, `pi` etc. 
* Calculus, algebra, plotting - `diff`, `integrate`, `limit`, `Sum`, `solve`, `plot`, `plot_implicit` etc.

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
* Complex numbers (`j`/`i`)

## Warranty
Provided "as is", without warranty of any kind 😊
