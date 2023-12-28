#!/usr/bin/env python

import setuptools
from pathlib import Path
import os

setuptools.setup(
    name='calcpy',
    author='Idan Pazi',
    author_email='idan.kp@gmail.com',
    url='https://github.com/idanp/calcpy',
    description='IPython based calculator', # fix this
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
        ## for parse_latex(): antlr4-python3-runtime (pip), antlr-python-runtime (conda)
    ],
    use_scm_version={'fallback_version':'0.0.0'},
    setup_requires=['setuptools_scm', 'ipython'], #TODO: move to pyproject.toml
    license='MIT License',
    zip_safe=False,
    keywords=['calculator',],
    entry_points = {
        "console_scripts": ['calcpy = calcpy.__main__:main']
    },
)
