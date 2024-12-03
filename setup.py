#!/usr/bin/env python

import setuptools
from pathlib import Path

setuptools.setup(
    name='calcpy',
    version='0.0.1',
    author='Idan Pazi',
    author_email='idan.kp@gmail.com',
    url='https://github.com/idanp/calcpy',
    description='Terminal calculator and advanced math solver using Python, IPython and SymPy',
    long_description=Path('README.md').read_text(),
    long_description_content_type='text/markdown',
    packages=['calcpy','previewer'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Framework :: IPython',
    ],
    install_requires=[
        'requests',
        'ipython',
        'pickleshare',
        'matplotlib',
        'sympy',
        'dateparser',
        'antlr4-python3-runtime==4.11', # todo: move to Lark when sympy supports it
    ],
    license='MIT License',
    zip_safe=False,
    keywords=['calculator',],
    entry_points = {
        "console_scripts": ['calcpy = calcpy.__main__:main']
    },
)
