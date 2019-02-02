def test_update_input_token(w3, contract, DAI_token, USDC_token, assert_fail):
    owner = w3.eth.defaultAccount
    user = w3.eth.accounts[1]

    assert contract.inputTokens(DAI_token.address)
    assert contract.inputTokens(USDC_token.address)

    # sender should be owner
    assert_fail(lambda: contract.updateInputToken(USDC_token.address, False, transact={'from': user}))
    assert contract.updateInputToken(USDC_token.address, False, transact={'from': owner})
    assert not contract.inputTokens(USDC_token.address)

    # can't remove unsupported token
    assert_fail(lambda: contract.updateInputToken(USDC_token.address, False, transact={'from': owner}))
    # can't add supported token
    assert_fail(lambda: contract.updateInputToken(DAI_token.address, True, transact={'from': owner}))

    assert_fail(lambda: contract.updateInputToken(USDC_token.address, True, transact={'from': user}))
    assert contract.updateInputToken(USDC_token.address, True, transact={'from': owner})
    assert contract.inputTokens(USDC_token.address)

def test_update_output_token(w3, contract, DAI_token, USDC_token, assert_fail):
    owner = w3.eth.defaultAccount
    user = w3.eth.accounts[1]

    assert contract.outputTokens(DAI_token.address)
    assert contract.outputTokens(USDC_token.address)

    # sender should be owner
    assert_fail(lambda: contract.updateOutputToken(USDC_token.address, False, transact={'from': user}))
    assert contract.updateOutputToken(USDC_token.address, False, transact={'from': owner})
    assert not contract.outputTokens(USDC_token.address)

    # can't remove unsupported token
    assert_fail(lambda: contract.updateOutputToken(USDC_token.address, False, transact={'from': owner}))
    # can't add supported token
    assert_fail(lambda: contract.updateOutputToken(DAI_token.address, True, transact={'from': owner}))

    assert_fail(lambda: contract.updateOutputToken(USDC_token.address, True, transact={'from': user}))
    assert contract.updateOutputToken(USDC_token.address, True, transact={'from': owner})
    assert contract.outputTokens(USDC_token.address)
