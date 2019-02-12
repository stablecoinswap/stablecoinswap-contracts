def test_oracle_url(w3, contract, assert_fail):
  owner = w3.eth.defaultAccount
  guest = w3.eth.accounts[1]

  # this function should be called by owner
  assert_fail(lambda: contract.updateTokenPriceOracleUrl('https://new-url.herokuapp.com', transact={'from': guest}))
  assert contract.updateTokenPriceOracleUrl(b'https://new-url.herokuapp.com', transact={'from': owner})
