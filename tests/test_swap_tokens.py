from tests.constants import (
    DEADLINE
)

def test_swap_tokens(w3, contract, oraclize, DAI_token, USDC_token, assert_fail):
    owner = w3.eth.defaultAccount
    oraclize_owner = w3.eth.accounts[1]
    user_address = w3.eth.accounts[2]

    INPUT_AMOUNT = 100 * 10**18 # 100 DAI
    SWAP_FEE = INPUT_AMOUNT * 0.003
    OUTPUT_AMOUNT = int((INPUT_AMOUNT - SWAP_FEE) / 10**(18-6))
    MIN_OUTPUT_AMOUNT = OUTPUT_AMOUNT - 1
    USDC_ADDED = 1000 * 10**6 # 1000 USDC
    QUERY_ID = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\xd2'

    DAI_token.transfer(user_address, 2*INPUT_AMOUNT, transact={})
    DAI_token.approve(contract.address, 2*INPUT_AMOUNT, transact={'from': user_address})
    USDC_token.transfer(w3.eth.defaultAccount, USDC_ADDED, transact={})
    USDC_token.approve(contract.address, USDC_ADDED, transact={'from': owner})

    assert contract.inputTokens(DAI_token.address)
    assert contract.outputTokens(USDC_token.address)
    # we don't have enough output tokens
    contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address})
    assert_fail(lambda: contract.__callback(QUERY_ID, '1000000', transact={'from': oraclize_owner}))

    contract.addLiquidity(USDC_token.address, USDC_ADDED, DEADLINE, transact={'from': owner})
    contract.__callback(QUERY_ID, str(USDC_ADDED*100), transact={'from': oraclize_owner})
    assert USDC_token.balanceOf(contract.address) == USDC_ADDED
    assert contract.totalSupply() == USDC_ADDED * 10**(18-6)
    assert contract.poolBalance() == USDC_ADDED * 10**(18-6)
    assert contract.balanceOf(owner) == USDC_ADDED * 10**(18-6)

    contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address})
    contract.__callback(QUERY_ID, '1000000', transact={'from': oraclize_owner})
    assert DAI_token.balanceOf(user_address) == 2 * INPUT_AMOUNT - INPUT_AMOUNT
    assert DAI_token.balanceOf(contract.address) == INPUT_AMOUNT
    assert USDC_token.balanceOf(user_address) == OUTPUT_AMOUNT
    assert USDC_token.balanceOf(contract.address) == USDC_ADDED - OUTPUT_AMOUNT
    assert contract.poolBalance() == USDC_ADDED * 10**(18-6) + SWAP_FEE
    owner_fee = INPUT_AMOUNT * 0.001
    total_supply_before = USDC_ADDED * 10**(18-6)
    # pool_balance_before = USDC_ADDED * 10**(18-6) + SWAP_FEE - owner_fee
    owner_shares = 99980003999200159 # total_supply_before * owner_fee / pool_balance_before
    assert contract.balanceOf(owner) == total_supply_before + owner_shares
    assert contract.totalSupply() == total_supply_before + owner_shares

    # input_amount > 0
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, 0, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))
    # min_output_amount > 0
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, 0, DEADLINE, transact={'from': user_address}))
    # output_amount >= min_output_amount
    contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, OUTPUT_AMOUNT + 1, DEADLINE, transact={'from': user_address})
    assert_fail(lambda: contract.__callback(QUERY_ID, '1000000', transact={'from': oraclize_owner}))
    # deadline < block.timestamp
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, 0, transact={'from': user_address}))
    # input_token and output_token should be allowed
    contract.updateOutputToken(USDC_token.address, False, transact={'from': owner})
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))
    contract.updateOutputToken(USDC_token.address, True, transact={'from': owner})
    contract.updateInputToken(DAI_token.address, False, transact={'from': owner})
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))
    contract.updateInputToken(DAI_token.address, True, transact={'from': owner})
    # permissions['tradingAllowed'] should be True
    contract.updatePermission(b'tradingAllowed', False, transact={'from': owner})
    assert_fail(lambda: contract.swapTokens(DAI_token.address, USDC_token.address, INPUT_AMOUNT, MIN_OUTPUT_AMOUNT, DEADLINE, transact={'from': user_address}))
    contract.updatePermission(b'tradingAllowed', True, transact={'from': owner})
