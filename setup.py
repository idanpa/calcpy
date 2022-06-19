#!/usr/bin/env python

import setuptools
from setuptools.command.install import install
import sys
import os
import IPython

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import calcpy

class post_setup(install):
    def run(self):
        install.run(self)
        try:
            calcpy_profile_path = IPython.paths.locate_profile(calcpy.CALCPY_PROFILE_NAME)
        except OSError:
            IPython.core.profiledir.ProfileDir.create_profile_dir_by_name(IPython.paths.get_ipython_dir(), calcpy.CALCPY_PROFILE_NAME)
            calcpy_profile_path = IPython.paths.locate_profile(calcpy.CALCPY_PROFILE_NAME)
        try:
            with open(os.path.join(calcpy_profile_path, 'startup', 'user_startup.py'), 'x') as f:
                f.write('def user_startup():\n    pass')
        except FileExistsError:
            pass

with open('README.md', 'r', encoding="utf8") as f:
    long_description = f.read()

setuptools.setup(
    name='calcpy',
    version='0.0.1',
    author='Idan Pazi',
    author_email='idan.kp@gmail.com',
    url='https://github.com/idanp/calcpy',
    description='IPython based calculator',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['calcpy'],
    py_modules=['calcpy_cli'],
    cmdclass={
        'install': post_setup,
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Framework :: IPython',
    ],
    install_requires=[
        'ipython', 'sympy', 'matplotlib'
        ## for dates: dateparser
        ## for parse_latex(): antlr4-python3-runtime (pip), antlr-python-runtime (conda)
    ],
    license='MIT License',
    zip_safe=False,
    keywords=['calculator',],
    entry_points = {
        "console_scripts": ['calcpy = calcpy_cli:main']
    },
)
