def test_token_support(w3, contract, DAI_token, USDC_token, assert_fail):
    owner = w3.eth.defaultAccount
    user = w3.eth.accounts[1]

    assert contract.supportedTokens(DAI_token.address)
    assert contract.supportedTokens(USDC_token.address)

    # sender should be owner
    assert_fail(lambda: contract.removeTokenSupport(USDC_token.address, transact={'from': user}))
    assert contract.removeTokenSupport(USDC_token.address, transact={'from': owner})
    assert not contract.supportedTokens(USDC_token.address)

    # can't remove unsupported token
    assert_fail(lambda: contract.removeTokenSupport(USDC_token.address, transact={'from': owner}))
    # can't add supported token
    assert_fail(lambda: contract.addTokenSupport(DAI_token.address, transact={'from': owner}))

    assert_fail(lambda: contract.addTokenSupport(USDC_token.address, transact={'from': user}))
    assert contract.addTokenSupport(USDC_token.address, transact={'from': owner})
    assert contract.supportedTokens(USDC_token.address)
