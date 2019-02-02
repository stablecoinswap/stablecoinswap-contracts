from tests.constants import (
    DEADLINE
)

def test_swap_tokens(w3, contract, DAI_token, USDC_token, assert_fail):
    user_address = w3.eth.accounts[1]

    INPUT_AMOUNT = 10000
    SWAP_FEE = INPUT_AMOUNT * 0.002
    OUTPUT_AMOUNT = INPUT_AMOUNT - SWAP_FEE
    PRICE_LIMIT = 1000000
    USDC_ADDED = 1000000000

    DAI_token.transfer(user_address, 2*INPUT_AMOUNT, transact={})
    DAI_token.approve(contract.address, 2*INPUT_AMOUNT, transact={'from': user_address})
    USDC_token.transfer(w3.eth.defaultAccount, USDC_ADDED, transact={})
    USDC_token.approve(contract.address, USDC_ADDED, transact={'from': w3.eth.defaultAccount})

    assert contract.inputTokens(DAI_token.address)
    assert contract.outputTokens(USDC_token.address)
    # we don't have enough output tokens
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, PRICE_LIMIT, DEADLINE, transact={'from': user_address}))

    contract.addLiquidity(USDC_token.address, USDC_ADDED, DEADLINE, transact={'from': w3.eth.defaultAccount})
    assert USDC_token.balanceOf(contract.address) == USDC_ADDED
    assert contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, PRICE_LIMIT, DEADLINE, transact={'from': user_address})
    assert DAI_token.balanceOf(contract.address) == INPUT_AMOUNT
    assert USDC_token.balanceOf(user_address) == OUTPUT_AMOUNT
    assert USDC_token.balanceOf(contract.address) == USDC_ADDED - OUTPUT_AMOUNT

    # input_amount > 0
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, 0, PRICE_LIMIT, DEADLINE, transact={'from': user_address}))
    # limit_price > 0
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, 0, DEADLINE, transact={'from': user_address}))
    # limit_price >= current_price
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, PRICE_LIMIT - 1, DEADLINE, transact={'from': user_address}))
    # deadline < block.timestamp
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, PRICE_LIMIT, 0, transact={'from': user_address}))
    # input_token and output_token should be allowed
    contract.updateOutputToken(USDC_token.address, False, transact={'from': w3.eth.defaultAccount})
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, PRICE_LIMIT, DEADLINE, transact={'from': user_address}))
    contract.updateOutputToken(USDC_token.address, True, transact={'from': w3.eth.defaultAccount})
    contract.updateInputToken(DAI_token.address, False, transact={'from': w3.eth.defaultAccount})
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, PRICE_LIMIT, DEADLINE, transact={'from': user_address}))
