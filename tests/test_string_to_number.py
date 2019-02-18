def test_string_to_number(contract):
  assert contract.stringToNumber('1') == 1
  assert contract.stringToNumber('1.0') == 1
  assert contract.stringToNumber('-1') == -1
  assert float(contract.stringToNumber('42.314')) == 42.314
  assert float(contract.stringToNumber('-15.025')) == -15.025

