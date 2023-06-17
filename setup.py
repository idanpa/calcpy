#!/usr/bin/env python

import setuptools
from setuptools.command.install import install
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

CALCPY_PROFILE_NAME = 'calcpy'

class post_setup(install):
    def run(self):
        install.run(self)
        import IPython
        try:
            calcpy_profile_path = IPython.paths.locate_profile(CALCPY_PROFILE_NAME)
        except OSError:
            IPython.core.profiledir.ProfileDir.create_profile_dir_by_name(IPython.paths.get_ipython_dir(), CALCPY_PROFILE_NAME)
            calcpy_profile_path = IPython.paths.locate_profile(CALCPY_PROFILE_NAME)
        try:
            with open(os.path.join(calcpy_profile_path, 'user_startup.py'), 'x') as f:
                f.write('# CalcPy user startup:')
        except FileExistsError:
            pass

setuptools.setup(
    name='calcpy',
    author='Idan Pazi',
    author_email='idan.kp@gmail.com',
    url='https://github.com/idanp/calcpy',
    description='IPython based calculator', # fix this
    long_description=Path('README.md').read_text(),
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
        'requests',
        'ipython',
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
        "console_scripts": ['calcpy = calcpy_cli:main']
    },
)
