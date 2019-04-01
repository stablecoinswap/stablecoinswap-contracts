from tests.constants import (
    DEADLINE
)

def test_initial_balances(w3, contract):
    a0, a1 = w3.eth.accounts[:2]
    # user
    assert contract.balanceOf(a1) == 0
    # contract
    assert contract.totalSupply() == 0

def test_initial_liquidity(w3, contract, DAI_token, assert_fail):
    oraclize_owner = w3.eth.accounts[1]
    user_address = w3.eth.accounts[2]
    DAI_token.transfer(user_address, 15*10**18, transact={})
    DAI_token.approve(contract.address, 15*10**18, transact={'from': user_address})
    assert DAI_token.balanceOf(user_address) == 15*10**18
    # initial liquidity value should be >= 10**9
    assert_fail(lambda: contract.addLiquidity(DAI_token.address, 10**9-1, DEADLINE, transact={'from': user_address}))
    DAI_ADDED = 10**9
    QUERY_ID = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\xd2'
    contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user_address})
    contract.__callback(QUERY_ID, '100000000100', transact={'from': oraclize_owner})
    assert DAI_token.balanceOf(contract.address) == DAI_ADDED
    assert contract.totalSupply() == DAI_ADDED + 1
    assert contract.balanceOf(user_address) == DAI_ADDED + 1
    assert contract.poolOwnership(user_address) == 1.0

def test_liquidity_pool(w3, contract, DAI_token, USDC_token, assert_fail):
    owner = w3.eth.accounts[0]
    oraclize_owner = w3.eth.accounts[1]
    user1 = w3.eth.accounts[2]
    user2 = w3.eth.accounts[3]
    DAI_token.transfer(user1, 15*10**18, transact={})
    DAI_token.approve(contract.address, 15*10**18, transact={'from': user1})
    DAI_ADDED = 10**18
    QUERY_ID = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\xd2'

    # permissions['liquidityAddingAllowed'] should be True
    assert contract.permissions(b'liquidityAddingAllowed')
    contract.updatePermission(b'liquidityAddingAllowed', False, transact={'from': owner})
    assert_fail(lambda: contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user1}))
    contract.updatePermission(b'liquidityAddingAllowed', True, transact={'from': owner})
    contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user1})
    contract.__callback(QUERY_ID, str(DAI_ADDED*100), transact={'from': oraclize_owner})

    USDC_token.transfer(user2, 15*10**6, transact={})
    USDC_token.approve(contract.address, 15*10**6, transact={'from': user2})
    USDC_ADDED = 3*10**6
    contract.addLiquidity(USDC_token.address, USDC_ADDED, DEADLINE, transact={'from': user2})
    contract.__callback(QUERY_ID, str(USDC_ADDED*100), transact={'from': oraclize_owner})

    assert contract.totalSupply() == DAI_ADDED + USDC_ADDED * 10**(18-6)
    assert contract.balanceOf(user1) == DAI_ADDED
    assert contract.balanceOf(user2) == USDC_ADDED * 10**(18-6) # we calculate contract balances in tokens with 18 decimals
    assert contract.poolOwnership(user1) == 0.25
    assert contract.poolOwnership(user2) == 0.75

    # deadline < block.timestamp
    assert_fail(lambda: contract.addLiquidity(DAI_token.address, DAI_ADDED, 1, transact={'from': user1}))
    # Can't transfer more liquidity than owned
    assert_fail(lambda: contract.transfer(user2, DAI_ADDED + 1, transact={'from': user1}))

    # Second liquidity provider (user2) transfers liquidity to first liquidity provider (user1)
    TRANSFERRED_AMOUNT = 10**18
    contract.transfer(user1, TRANSFERRED_AMOUNT, transact={'from': user2})
    assert contract.balanceOf(user1) == DAI_ADDED + TRANSFERRED_AMOUNT
    assert contract.balanceOf(user2) == USDC_ADDED * 10**(18-6) - TRANSFERRED_AMOUNT
    assert contract.poolOwnership(user1) == 0.5
    assert contract.poolOwnership(user2) == 0.5
    assert DAI_token.balanceOf(contract.address) == DAI_ADDED
    assert USDC_token.balanceOf(contract.address) == USDC_ADDED

    # amount > owned (liquidity)
    contract.removeLiquidity(USDC_token.address, USDC_ADDED * 10**(18-6) - TRANSFERRED_AMOUNT + 1, DEADLINE, transact={'from': user2})
    assert_fail(lambda: contract.__callback(QUERY_ID, str((USDC_ADDED * 10**(18-6) - TRANSFERRED_AMOUNT + 1) * 100), transact={'from': oraclize_owner}))
    # deadline < block.timestamp
    assert_fail(lambda: contract.removeLiquidity(USDC_token.address, TRANSFERRED_AMOUNT, 1, transact={'from': user2}))
    # amount > token liquidity
    contract.removeLiquidity(DAI_token.address, DAI_ADDED + 1, DEADLINE, transact={'from': user2})
    assert_fail(lambda: contract.__callback(QUERY_ID, str((DAI_ADDED + 1) * 100), DEADLINE, transact={'from': oraclize_owner}))

    # permissions['liquidityRemovingAllowed'] should be True
    assert contract.permissions(b'liquidityRemovingAllowed')
    contract.updatePermission(b'liquidityRemovingAllowed', False, transact={'from': owner})
    assert_fail(lambda: contract.removeLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user2}))
    contract.updatePermission(b'liquidityRemovingAllowed', True, transact={'from': owner})

    # First and second liquidity providers remove their remaining liquidity
    contract.removeLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user2})
    contract.__callback(QUERY_ID, str(DAI_ADDED*100), transact={'from': oraclize_owner})
    contract.removeLiquidity(USDC_token.address, int(USDC_ADDED - TRANSFERRED_AMOUNT / 10**(18-6) - DAI_ADDED / 10**(18-6)), DEADLINE, transact={'from': user2})
    contract.__callback(QUERY_ID, str(int((USDC_ADDED - TRANSFERRED_AMOUNT / 10**(18-6) - DAI_ADDED / 10**(18-6)) * 100)), transact={'from': oraclize_owner})
    assert contract.poolOwnership(user2) == 0
    assert contract.poolOwnership(user1) == 1
    contract.removeLiquidity(USDC_token.address, int((DAI_ADDED + TRANSFERRED_AMOUNT) / 10**(18-6)), DEADLINE, transact={'from': user1})
    contract.__callback(QUERY_ID, str(int((DAI_ADDED + TRANSFERRED_AMOUNT) / 10**(18-6) * 100)), transact={'from': oraclize_owner})
    assert contract.totalSupply() == 0
    assert contract.balanceOf(user1) == 0
    assert contract.balanceOf(user2) == 0
    assert USDC_token.balanceOf(user1) == (DAI_ADDED + TRANSFERRED_AMOUNT) /  10**(18-6)
    assert DAI_token.balanceOf(user2) == DAI_ADDED
    assert DAI_token.balanceOf(contract.address) == 0
    assert USDC_token.balanceOf(contract.address) == 0

    # Can add liquidity again after all liquidity is divested
    contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user1})
    contract.__callback(QUERY_ID, str(DAI_ADDED*100), transact={'from': oraclize_owner})
