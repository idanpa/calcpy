def test_currency(ip):
    ip.run_cell('calcpy.update_currency()')
    res = ip.run_cell('10gbp').result
    base_cur = ip.run_cell('calcpy.base_currency').result
    assert str(res.args[1]) == base_cur


