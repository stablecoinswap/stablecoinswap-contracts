def test_update_input_token(w3, contract, DAI_token, USDC_token, assert_fail):
    owner = w3.eth.defaultAccount
    user = w3.eth.accounts[1]

    assert DAI_token.address in contract.availableInputTokens()
    assert USDC_token.address in contract.availableInputTokens()

    # sender should be owner
    assert_fail(lambda: contract.updateInputToken(USDC_token.address, False, transact={'from': user}))
    assert contract.updateInputToken(USDC_token.address, False, transact={'from': owner})
    assert not USDC_token.address in contract.availableInputTokens()

    # can't remove unsupported token
    assert_fail(lambda: contract.updateInputToken(USDC_token.address, False, transact={'from': owner}))
    # can't add supported token
    assert_fail(lambda: contract.updateInputToken(DAI_token.address, True, transact={'from': owner}))

    assert_fail(lambda: contract.updateInputToken(USDC_token.address, True, transact={'from': user}))
    assert contract.updateInputToken(USDC_token.address, True, transact={'from': owner})
    assert USDC_token.address in contract.availableInputTokens()

def test_update_output_token(w3, contract, DAI_token, USDC_token, assert_fail):
    owner = w3.eth.defaultAccount
    user = w3.eth.accounts[1]

    assert DAI_token.address in contract.availableOutputTokens()
    assert USDC_token.address in contract.availableOutputTokens()

    # sender should be owner
    assert_fail(lambda: contract.updateOutputToken(USDC_token.address, False, transact={'from': user}))
    assert contract.updateOutputToken(USDC_token.address, False, transact={'from': owner})
    assert not USDC_token.address in contract.availableOutputTokens()

    # can't remove unsupported token
    assert_fail(lambda: contract.updateOutputToken(USDC_token.address, False, transact={'from': owner}))
    # can't add supported token
    assert_fail(lambda: contract.updateOutputToken(DAI_token.address, True, transact={'from': owner}))

    assert_fail(lambda: contract.updateOutputToken(USDC_token.address, True, transact={'from': user}))
    assert contract.updateOutputToken(USDC_token.address, True, transact={'from': owner})
    assert USDC_token.address in contract.availableOutputTokens()
