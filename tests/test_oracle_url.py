def test_oracle_url(w3, contract, assert_fail):
  owner = w3.eth.defaultAccount
  guest = w3.eth.accounts[1]

  # this function should be called by owner
  assert_fail(lambda: contract.updateTokenPriceOracleUrl('https://new-url.herokuapp.com', transact={'from': guest}))
  assert contract.updateTokenPriceOracleUrl('https://new-url.herokuapp.com', transact={'from': owner})

def test_create_url(w3, contract, DAI_token, USDC_token):
    input_address = DAI_token.address.upper().replace('X', 'x')
    output_address = USDC_token.address.upper().replace('X', 'x')
    test_string = 'https://fake-url.herokuapp.com?base_token_address=' + input_address + '&quote_token_address=' + output_address

    result = contract.createOracleUrl(DAI_token.address, USDC_token.address)
    assert result == test_string
