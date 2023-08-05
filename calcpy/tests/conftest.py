import sys
import os
import pytest
from IPython.testing.globalipapp import start_ipython

# take calcpy from here:
sys.path.insert(0, os.path.join(sys.path[0], '..'))

@pytest.fixture(scope='session')
def session_ip():
    ip = start_ipython()
    ip.run_line_magic('load_ext', 'calcpy')
    return ip

@pytest.fixture(scope='function')
def ip(session_ip):
    session_ip.calcpy.reset(prompt=False)
    return session_ip
