from tests.constants import (
    ZERO_ADDR
)

def test_oraclize_address_resolver(w3, oraclize_address_resolver, oraclize):
    owner = w3.eth.defaultAccount
    guest = w3.eth.accounts[1]
    oraclize_addr = oraclize.address

    assert oraclize_address_resolver.getAddress() == oraclize_addr

def test_oraclize_connector(w3, oraclize, assert_fail):
    owner = w3.eth.defaultAccount
    cur_time = w3.eth.getBlock(w3.eth.blockNumber).timestamp

    assert oraclize.getPrice(b'URL') == 0
    oraclize.addCbAddress(owner, b'\x01', transact={'from': owner})
    assert oraclize.cbAddress() == owner
    assert oraclize.getPrice(b'URL') == 4000000000000000

    assert w3.eth.getBalance(oraclize.address) == 0
    assert w3.eth.getBalance(owner) == w3.toWei(1000000, 'ether')
    w3.eth.sendTransaction({'to': oraclize.address, 'value': w3.toWei(2.0, 'ether')})
    assert w3.eth.getBalance(oraclize.address) == 2*10**18

    result = oraclize.query(cur_time, b'URL', 'https://fake-url.herokuapp.com')
    assert result == b'.Z\xda\xe6)\x98\xcd\x9b\x16\x07\xedA\x02W/lK\xdb\xe4\xb4\xaa\x99o\x14\x99\xf4A(\xbc|\x10\xbe'

def test_oraclize_address(w3, contract, oraclize, assert_fail):
    owner = w3.eth.defaultAccount
    user = w3.eth.accounts[2]

    assert contract.oraclizeAddress == oraclize.address
    assert_fail(lambda: contract.updateOraclizeAddress(w3.eth.accounts[1], transact={'from': user}))
    contract.updateOraclizeAddress(w3.eth.accounts[1], transact={'from': owner})
    assert contract.oraclizeAddress == w3.eth.accounts[1]
