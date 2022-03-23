## CalcPy on Android
1. Install [termux](https://termux.com/) using [APK](https://github.com/termux/termux-app/releases) or using [F-Droid](https://f-droid.org/en/packages/com.termux/) (Play Store version is outdated)
2. On termux install requirements:
```
pkg install python 
pkg install matplotlib
pip install numpy sympy
LDFLAGS="-L/system/lib64/" CFLAGS="-I/data/data/com.termux/files/usr/include/" pip install Pillow
```
3. Then install calcpy
```
pip install git+https://github.com/idanpa/calcpy
```

<!-- https://stackoverflow.com/questions/62956054/how-to-install-pillow-on-termux -->
<!-- https://wiki.termux.com/wiki/Python#Python_module_installation_tips_and_tricks -->
<!-- need to set the font to something with normal dot operator (see 2x output) -->
<!-- suggest setting that would have all the math operations on keyboard? -->
