def test_store_restore(ip):
    ip.run_cell('test_var = 100')
    assert 'test_var' in ip.user_ns
    ip.run_cell('calcpy.auto_store = False')
    ip.run_cell('del test_var')
    assert 'test_var' not in ip.user_ns
    ip.run_cell('calcpy.auto_store = True')
    assert 'test_var' in ip.user_ns
    assert ip.run_cell('test_var').result == 100


