def test_permissions(w3, contract, assert_fail):
  owner = w3.eth.defaultAccount
  user = w3.eth.accounts[1]

  # after initialization
  assert contract.permissions('liquidityAddingAllowed')
  assert contract.permissions('tradingAllowed')

  # only owner can change permission
  assert_fail(lambda: contract.updatePermission('liquidityAddingAllowed', False, transact={'from': user}))
  contract.updatePermission('liquidityAddingAllowed', False, transact={'from': owner})
  assert not contract.permissions('liquidityAddingAllowed')

  # after permission was disabled it's possible to enable it again
  contract.updatePermission('liquidityAddingAllowed', True, transact={'from': owner})
  assert contract.permissions('liquidityAddingAllowed')
