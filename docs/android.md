## CalcPy on Android (Termux)
0. Install [Termux](https://termux.com/) using [APK](https://github.com/termux/termux-app/releases) or using [F-Droid](https://f-droid.org/en/packages/com.termux/) (Play Store version is outdated)
1. Install requirements:
```
pkg install build-essential libandroid-spawn libjpeg-turbo git
pkg install python python-pip python-numpy
pip install ipython sympy requests dateparser tzdata pickleshare
```
2. Install CalcPy (ignore dependencies)
```
pip install --no-deps git+https://github.com/idanpa/calcpy
```
