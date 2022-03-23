#!/usr/bin/env python

import setuptools
from setuptools.command.install import install
import subprocess
import shutil
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import calcpy

class post_setup(install):
    def run(self):
        install.run(self)
        print('Installing calcpy profile')
        # TODO: do it with the ipython module (in python), would make sure it is using the ipython of the existing env
        if shutil.which('ipython') is None:
            raise ValueError('IPython was not found, abort')
        p = subprocess.run(['ipython', 'locate', 'profile', calcpy.CALCPY_PROFILE_NAME], stdout=subprocess.PIPE)
        if p.returncode == 0:
            calcpy_profile_path = p.stdout.decode()
            print(f'calcpy profile already exist in {calcpy_profile_path}')
        else:
            print('CalcPy IPython profile was not found, creating profile.')
            p = subprocess.run(['ipython', 'profile', 'create', calcpy.CALCPY_PROFILE_NAME], stdout=subprocess.PIPE)
            if p.returncode != 0:
                raise ValueError('CalcPy IPython profile creation failed')

            p = subprocess.run(['ipython', 'locate', 'profile', calcpy.CALCPY_PROFILE_NAME], stdout=subprocess.PIPE)
            calcpy_profile_path = p.stdout.decode()
            print(f'calcpy profile is in {calcpy_profile_path}')

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
