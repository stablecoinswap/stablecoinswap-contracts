from decimal import (
    Decimal,
)

from tests.constants import (
    DEADLINE
)

def test_swap_tokens(w3, contract, price_oracle, DAI_token, USDC_token, assert_fail):
    owner = w3.eth.defaultAccount
    user_address = w3.eth.accounts[1]

    DAI_ADDED = 2 * 10**18 # 2 DAI
    INPUT_AMOUNT = 1 * 10**18 # 1 DAI
    DAI_TOKEN_PRICE = int(1.05 * 10**8)
    USDC_TOKEN_PRICE = 1 * 10**8
    SWAP_FEE = INPUT_AMOUNT * DAI_TOKEN_PRICE / USDC_TOKEN_PRICE * 0.002
    OUTPUT_AMOUNT = int(INPUT_AMOUNT * DAI_TOKEN_PRICE / USDC_TOKEN_PRICE - SWAP_FEE) / 10**(18-6)
    MIN_OUTPUT_AMOUNT = int(OUTPUT_AMOUNT) - 1
    USDC_ADDED = 2 * 10**6 # 2 DAI

    DAI_token.transfer(user_address, DAI_ADDED, transact={})
    DAI_token.approve(contract.address, DAI_ADDED, transact={'from': user_address})
    USDC_token.transfer(w3.eth.defaultAccount, USDC_ADDED, transact={})
    USDC_token.approve(contract.address, USDC_ADDED, transact={'from': owner})
    price_oracle.updatePrice(DAI_token.address, DAI_TOKEN_PRICE, transact={'from': owner})
    price_oracle.updatePrice(USDC_token.address, USDC_TOKEN_PRICE, transact={'from': owner})

    assert contract.inputTokens(DAI_token.address)
    assert contract.outputTokens(USDC_token.address)
    # we don't have enough output tokens
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))

    contract.addLiquidity(USDC_token.address, USDC_ADDED, DEADLINE, transact={'from': owner})
    assert USDC_token.balanceOf(contract.address) == USDC_ADDED

    contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address})
    assert DAI_token.balanceOf(user_address) == DAI_ADDED - INPUT_AMOUNT
    assert DAI_token.balanceOf(contract.address) == INPUT_AMOUNT
    assert USDC_token.balanceOf(user_address) == OUTPUT_AMOUNT
    assert USDC_token.balanceOf(contract.address) == USDC_ADDED - OUTPUT_AMOUNT

    # input_amount > 0
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, 0, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))
    # min_output_amount > 0
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, 0, DEADLINE, transact={'from': user_address}))
    # output_amount >= min_output_amount
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, OUTPUT_AMOUNT + 1, DEADLINE, transact={'from': user_address}))
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
