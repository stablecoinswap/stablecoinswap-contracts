from decimal import (
    Decimal,
)

from tests.constants import (
    DEADLINE, MAX_GAS_USED
)

def test_swap_tokens(w3, contract, price_oracle, DAI_token, GUSD_token, assert_fail):
    owner = w3.eth.defaultAccount
    user_address = w3.eth.accounts[1]

    DAI_ADDED = 2 * 10**18 # 2 DAI
    INPUT_AMOUNT = 1 * 10**18 # 1 DAI
    DAI_TOKEN_PRICE = int(1.05 * 10**8)
    GUSD_TOKEN_PRICE = 1 * 10**8
    SWAP_FEE = INPUT_AMOUNT * DAI_TOKEN_PRICE / GUSD_TOKEN_PRICE * 0.003
    OUTPUT_AMOUNT = int((INPUT_AMOUNT * DAI_TOKEN_PRICE / GUSD_TOKEN_PRICE - SWAP_FEE) / 10**(18-2))
    MIN_OUTPUT_AMOUNT = int(OUTPUT_AMOUNT) - 1
    GUSD_ADDED = 2 * 10**2 # 2 GUSD

    DAI_token.transfer(user_address, DAI_ADDED, transact={})
    DAI_token.approve(contract.address, DAI_ADDED, transact={'from': user_address})
    GUSD_token.transfer(w3.eth.defaultAccount, GUSD_ADDED, transact={})
    GUSD_token.approve(contract.address, GUSD_ADDED, transact={'from': owner})
    price_oracle.updatePrice(DAI_token.address, DAI_TOKEN_PRICE, transact={'from': owner})
    price_oracle.updatePrice(GUSD_token.address, GUSD_TOKEN_PRICE * 10**16, transact={'from': owner})
    price_oracle.updateTokenAddress(DAI_token.address, 0, transact={'from': owner})
    price_oracle.updateTokenAddress(GUSD_token.address, 1, transact={'from': owner})

    assert contract.inputTokens(DAI_token.address)
    assert contract.outputTokens(GUSD_token.address)
    # we don't have enough output tokens
    assert_fail(lambda: contract.swapTokens(DAI_token.address, GUSD_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))

    contract.addLiquidity(GUSD_token.address, GUSD_ADDED, DEADLINE, transact={'from': owner})
    assert GUSD_token.balanceOf(contract.address) == GUSD_ADDED
    assert contract.totalSupply() == GUSD_ADDED * 10**(18-2)
    assert price_oracle.poolSize(contract.address) == GUSD_ADDED * 10**(18-2)
    assert contract.balanceOf(owner) == GUSD_ADDED * 10**(18-2)

    tx_hash = contract.swapTokens(DAI_token.address, GUSD_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address})
    transaction = w3.eth.getTransactionReceipt(tx_hash)
    assert transaction['gasUsed'] < MAX_GAS_USED

    assert DAI_token.balanceOf(user_address) == DAI_ADDED - INPUT_AMOUNT
    assert DAI_token.balanceOf(contract.address) == INPUT_AMOUNT
    assert GUSD_token.balanceOf(user_address) == OUTPUT_AMOUNT
    assert GUSD_token.balanceOf(contract.address) == GUSD_ADDED - OUTPUT_AMOUNT
    # pool_size = 1 DAI * 1.05 + 0.96 GUSD * 1 = 2.01 STL
    assert price_oracle.poolSize(contract.address) == INPUT_AMOUNT * DAI_TOKEN_PRICE * 10**(18-18) / 10**8 + (GUSD_ADDED - OUTPUT_AMOUNT) * GUSD_TOKEN_PRICE * 10**(18-2) / 10**8
    # owner_fee = INPUT_AMOUNT * DAI_TOKEN_PRICE / GUSD_TOKEN_PRICE * 0.001
    total_supply_before = GUSD_ADDED * 10**(18-2)
    # pool_balance_before = GUSD_ADDED * 10**(18-6) + (SWAP_FEE - owner_fee) * GUSD_TOKEN_PRICE
    owner_shares = 1048898656410768 # total_supply_before * owner_fee / pool_balance_before
    assert contract.balanceOf(owner) == total_supply_before + owner_shares
    assert contract.totalSupply() == total_supply_before + owner_shares

    # input_amount > 0
    assert_fail(lambda: contract.swapTokens(DAI_token.address, GUSD_token.address, 0, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))
    # min_output_amount > 0
    assert_fail(lambda: contract.swapTokens(DAI_token.address, GUSD_token.address, INPUT_AMOUNT, 0, DEADLINE, transact={'from': user_address}))
    # output_amount >= min_output_amount
    assert_fail(lambda: contract.swapTokens(DAI_token.address, GUSD_token.address, INPUT_AMOUNT, OUTPUT_AMOUNT + 1, DEADLINE, transact={'from': user_address}))
    # deadline < block.timestamp
    assert_fail(lambda: contract.swapTokens(DAI_token.address, GUSD_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, 0, transact={'from': user_address}))
    # input_token and output_token should be allowed
    contract.updateOutputToken(GUSD_token.address, False, transact={'from': owner})
    assert_fail(lambda: contract.swapTokens(DAI_token.address, GUSD_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))
    contract.updateOutputToken(GUSD_token.address, True, transact={'from': owner})
    contract.updateInputToken(DAI_token.address, False, transact={'from': owner})
    assert_fail(lambda: contract.swapTokens(DAI_token.address, GUSD_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))
    contract.updateInputToken(DAI_token.address, True, transact={'from': owner})
    # permissions['tradingAllowed'] should be True
    contract.updatePermission('tradingAllowed', False, transact={'from': owner})
    assert_fail(lambda: contract.swapTokens(DAI_token.address, GUSD_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))
    contract.updatePermission('tradingAllowed', True, transact={'from': owner})
