from tests.constants import (
    DEADLINE
)

def test_swap_tokens(w3, contract, oraclize, DAI_token, USDC_token, assert_fail):
    oraclize_owner = w3.eth.accounts[1]
    user_address = w3.eth.accounts[2]

    INPUT_AMOUNT = 10**9
    SWAP_FEE = INPUT_AMOUNT * 0.002
    OUTPUT_AMOUNT = int(INPUT_AMOUNT - SWAP_FEE)
    MIN_OUTPUT_AMOUNT = OUTPUT_AMOUNT - 1
    USDC_ADDED = 10**12
    BYTES32_EMPTY_VALUE = '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    DAI_token.transfer(user_address, 2*INPUT_AMOUNT, transact={})
    DAI_token.approve(contract.address, 2*INPUT_AMOUNT, transact={'from': user_address})
    USDC_token.transfer(w3.eth.defaultAccount, USDC_ADDED, transact={})
    USDC_token.approve(contract.address, USDC_ADDED, transact={'from': w3.eth.defaultAccount})

    assert contract.inputTokens(DAI_token.address)
    assert contract.outputTokens(USDC_token.address)
    # we don't have enough output tokens
    contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address})
    assert contract.lastQueryId() != BYTES32_EMPTY_VALUE
    assert_fail(lambda: contract.__callback(contract.lastQueryId(), '1000000', transact={'from': oraclize_owner}))

    contract.addLiquidity(USDC_token.address, USDC_ADDED, DEADLINE, transact={'from': w3.eth.defaultAccount})
    assert USDC_token.balanceOf(contract.address) == USDC_ADDED

    contract.__callback(contract.lastQueryId(), '1000000', transact={'from': oraclize_owner})
    assert DAI_token.balanceOf(user_address) == 2 * INPUT_AMOUNT - INPUT_AMOUNT
    assert DAI_token.balanceOf(contract.address) == INPUT_AMOUNT
    assert USDC_token.balanceOf(user_address) == OUTPUT_AMOUNT
    assert USDC_token.balanceOf(contract.address) == USDC_ADDED - OUTPUT_AMOUNT

    # input_amount > 0
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, 0, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))
    # min_output_amount > 0
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, 0, DEADLINE, transact={'from': user_address}))
    # output_amount >= min_output_amount
    contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, OUTPUT_AMOUNT + 1, DEADLINE, transact={'from': user_address})
    assert_fail(lambda: contract.__callback(contract.lastQueryId(), '1000000', transact={'from': oraclize_owner}))
    # deadline < block.timestamp
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, 0, transact={'from': user_address}))
    # input_token and output_token should be allowed
    contract.updateOutputToken(USDC_token.address, False, transact={'from': w3.eth.defaultAccount})
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))
    contract.updateOutputToken(USDC_token.address, True, transact={'from': w3.eth.defaultAccount})
    contract.updateInputToken(DAI_token.address, False, transact={'from': w3.eth.defaultAccount})
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))
    contract.updateInputToken(DAI_token.address, True, transact={'from': w3.eth.defaultAccount})
    # permissions['tradingAllowed'] should be True
    contract.updatePermission(b'tradingAllowed', False, transact={'from': w3.eth.defaultAccount})
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))
    contract.updatePermission(b'tradingAllowed', True, transact={'from': w3.eth.defaultAccount})
