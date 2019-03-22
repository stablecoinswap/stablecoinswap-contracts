def test_oracle_url(w3, contract, assert_fail):
  owner = w3.eth.defaultAccount
  guest = w3.eth.accounts[1]

  # update functions should be called by owner
  assert_fail(lambda: contract.updateTokenPriceOracleUrl('https://new-url.herokuapp.com', transact={'from': guest}))
  assert_fail(lambda: contract.updateLiquidityOracleUrl('https://new-url.herokuapp.com', transact={'from': guest}))
  assert contract.updateTokenPriceOracleUrl('https://new-url.herokuapp.com', transact={'from': owner})
  assert contract.updateLiquidityOracleUrl('https://new-url2.herokuapp.com', transact={'from': owner})

def test_token_price_params(w3, contract, DAI_token, USDC_token):
    input_address = DAI_token.address.upper().replace('X', 'x')
    output_address = USDC_token.address.upper().replace('X', 'x')
    test_string = '{"base_token_address":"' + input_address + '", "quote_token_address":"' + output_address + '"}'

    result = contract.createConversionParamsString(DAI_token.address, USDC_token.address)
    assert result == test_string

def test_liquidity_params(w3, contract, DAI_token):
    input_address = DAI_token.address.upper().replace('X', 'x')
    amount = 10**9
    test_string = '{"token_address":"' + input_address + '", "amount":"' + str(amount) + '"}'

    result = contract.createLiquidityParamsString(DAI_token.address, amount, False)
    assert result == test_string

    test_string = '{"token_address":"' + input_address + '", "amount":"-' + str(amount) + '"}'

    result = contract.createLiquidityParamsString(DAI_token.address, amount, True)
    assert result == test_string
