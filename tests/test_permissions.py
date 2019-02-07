def test_permissions(w3, contract, assert_fail):
  owner = w3.eth.defaultAccount
  user = w3.eth.accounts[1]

  # after initialization
  assert contract.permissions(b'liquidityAddingAllowed')
  assert contract.permissions(b'liquidityRemovingAllowed')
  assert contract.permissions(b'tradingAllowed')

  contract.updatePermission(b'liquidityAddingAllowed', False, transact={'from': owner})
  assert not contract.permissions(b'liquidityAddingAllowed')

  # only owner can change permission
  assert_fail(lambda: contract.updatePermission(b'liquidityRemovingAllowed', False, transact={'from': user}))
  contract.updatePermission(b'liquidityRemovingAllowed', False)
  assert contract.permissions(b'liquidityRemovingAllowed')

  # after permission was disabled it's possible to enable it again
  contract.updatePermission(b'liquidityAddingAllowed', True, transact={'from': owner})
  assert contract.permissions(b'liquidityAddingAllowed')
