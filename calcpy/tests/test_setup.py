import os
import pytest
import tempfile
import venv
import shutil
import subprocess

@pytest.fixture
def venv_dir():
    p = tempfile.mkdtemp()
    yield p
    shutil.rmtree(p)

def test_setup(venv_dir):
    venv.create(venv_dir, with_pip=True, upgrade_deps=True, symlinks=True)
    dot_ipython_dir = os.path.join(venv_dir,'.ipython')
    os.environ['IPYTHONDIR'] = dot_ipython_dir
    calcpy_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    if os.name == 'nt':
        activate = os.path.join(venv_dir, 'Scripts', 'activate.bat') + ' & '
    else:
        activate = '. ' + os.path.join(venv_dir, 'bin', 'activate') + ' && '

    def check_output(cmd):
        return subprocess.check_output(activate + cmd, shell=True, text=True)

    assert venv_dir in check_output('pip --version')
    check_output('pip install ' + calcpy_path)
    assert 'Out[1]: 2' in check_output('calcpy -c 1+1')
    assert 'Out[1]: 2' in check_output('python -m calcpy -c 1+1')
