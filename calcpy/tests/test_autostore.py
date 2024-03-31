from sympy.abc import x

def test_store_restore_var(ip):
    ip.run_cell('test_var = 100')
    assert 'test_var' in ip.user_ns
    ip.run_cell('calcpy.auto_store = False')
    ip.run_cell('del test_var')
    assert 'test_var' not in ip.user_ns
    ip.run_cell('calcpy.auto_store = True')
    assert 'test_var' in ip.user_ns
    assert ip.run_cell('test_var').result == 100

def test_store_del_no_restore(ip):
    ip.run_cell('test_var = 100')
    assert 'test_var' in ip.user_ns
    ip.run_cell('del test_var')
    ip.run_cell('calcpy.auto_store = False')
    ip.run_cell('calcpy.auto_store = True')
    assert 'test_var' not in ip.user_ns

def test_store_restore_func(ip):
    ip.run_cell('def test_func():\n  return 100')
    ip.run_cell('calcpy.auto_store = False')
    ip.run_cell('del test_func')
    assert 'test_func' not in ip.user_ns
    ip.run_cell('calcpy.auto_store = True')
    assert ip.run_cell('test_func()').result == 100

def test_store_autovars(ip):
    ip.run_cell('x + 1') # generate autovar
    ip.run_cell('x=1') # set it to something else
    ip.run_cell('calcpy.auto_store = False')
    ip.run_cell('calcpy.auto_store = True')
    assert ip.run_cell('x').result == 1
    ip.run_cell('del x') # set it back to be autovar
    ip.run_cell('x + 1')
    ip.run_cell('calcpy.auto_store = False')
    ip.run_cell('calcpy.auto_store = True')
    assert ip.run_cell('x').result == x

