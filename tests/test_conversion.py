def test_string_to_number(contract):
    assert contract.stringToNumber('1') == 1
    assert contract.stringToNumber('10') == 10
    assert contract.stringToNumber('123456789') == 123456789

def test_address_to_string(w3, contract):
    address_string = w3.eth.accounts[1].upper().replace('X', 'x')
    assert contract.addressToString(w3.eth.accounts[1]) == address_string

def test_number_to_string(contract):
    assert contract.numberToString(0) == '0'
    assert contract.numberToString(1234567890) == '1234567890'
    assert contract.numberToString(-1) == '-1'
    assert contract.numberToString(170141183460469231731687303715884105727) == '170141183460469231731687303715884105727'
    assert contract.numberToString(-170141183460469231731687303715884105727) == '-170141183460469231731687303715884105727'
