from decimal import (
    Decimal,
)

from tests.constants import (
    DEADLINE
)

def test_initial_balances(w3, contract):
    a0, a1 = w3.eth.accounts[:2]
    # user
    assert contract.balanceOf(a1) == 0
    # contract
    assert contract.totalSupply() == 0

def test_initial_liquidity(w3, contract, DAI_token, price_oracle, assert_fail):
    owner = w3.eth.defaultAccount
    user_address = w3.eth.accounts[1]
    DAI_token.transfer(user_address, 15*10**18, transact={})
    DAI_token.approve(contract.address, 15*10**18, transact={'from': user_address})
    assert DAI_token.balanceOf(user_address) == 15*10**18
    price_oracle.updatePrice(DAI_token.address, 1 * 10**8, transact={'from': owner})

    # initial liquidity value should be >= 10**9
    assert_fail(lambda: contract.addLiquidity(DAI_token.address, 10**9-1, DEADLINE, transact={'from': user_address}))
    DAI_ADDED = 10**9
    price_oracle.updatePrice(DAI_token.address, int(1.01 * 10**8), transact={'from': owner})
    contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user_address})
    assert DAI_token.balanceOf(contract.address) == DAI_ADDED
    assert contract.totalSupply() == DAI_ADDED * 1.01
    assert contract.balanceOf(user_address) == DAI_ADDED * 1.01
    assert contract.poolOwnership(user_address) == 1.0

def test_liquidity_pool(w3, contract, DAI_token, USDC_token, price_oracle, assert_fail):
    owner = w3.eth.accounts[0]
    user1 = w3.eth.accounts[1]
    user2 = w3.eth.accounts[2]
    TOKEN_PRICE = 1.01
    INT_TOKEN_PRICE =  int(TOKEN_PRICE * 10**8)
    DAI_token.transfer(user1, 15*10**18, transact={})
    DAI_token.approve(contract.address, 15*10**18, transact={'from': user1})
    DAI_ADDED = 1 * 10**18 # 1 DAI
    price_oracle.updatePrice(DAI_token.address, INT_TOKEN_PRICE, transact={'from': owner})

    # permissions['liquidityAddingAllowed'] should be True
    assert contract.permissions(b'liquidityAddingAllowed')
    contract.updatePermission(b'liquidityAddingAllowed', False, transact={'from': owner})
    assert_fail(lambda: contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user1}))
    contract.updatePermission(b'liquidityAddingAllowed', True, transact={'from': owner})
    contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user1})

    USDC_token.transfer(user2, 15*10**6, transact={})
    USDC_token.approve(contract.address, 15*10**6, transact={'from': user2})
    USDC_ADDED = 3 * 10**6 # 3 USDC
    price_oracle.updatePrice(USDC_token.address, INT_TOKEN_PRICE, transact={'from': owner})
    contract.addLiquidity(USDC_token.address, USDC_ADDED, DEADLINE, transact={'from': user2})

    assert contract.totalSupply() == (DAI_ADDED + USDC_ADDED * 10**(18-6)) * TOKEN_PRICE
    assert contract.balanceOf(user1) == DAI_ADDED * TOKEN_PRICE
    assert contract.balanceOf(user2) == USDC_ADDED * 10**(18-6) * TOKEN_PRICE
    assert contract.poolOwnership(user1) == 0.25
    assert contract.poolOwnership(user2) == 0.75

    # deadline < block.timestamp
    assert_fail(lambda: contract.addLiquidity(DAI_token.address, DAI_ADDED, 1, transact={'from': user1}))
    # Can't transfer more liquidity than owned
    assert contract.balanceOf(user1) == DAI_ADDED * TOKEN_PRICE
    assert_fail(lambda: contract.transfer(user2, int(DAI_ADDED * TOKEN_PRICE) + 1, transact={'from': user1}))

    # Second liquidity provider (user2) transfers liquidity to first liquidity provider (user1)
    TRANSFERRED_AMOUNT = int(DAI_ADDED * TOKEN_PRICE)
    contract.transfer(user1, TRANSFERRED_AMOUNT, transact={'from': user2})
    NEW_USER_ONE_BALANCE = int(DAI_ADDED * TOKEN_PRICE) + TRANSFERRED_AMOUNT
    NEW_USER_TWO_BALANCE = int(USDC_ADDED * 10**(18-6) * TOKEN_PRICE) - TRANSFERRED_AMOUNT
    assert contract.balanceOf(user1) == NEW_USER_ONE_BALANCE
    assert contract.balanceOf(user2) == NEW_USER_TWO_BALANCE
    assert contract.poolOwnership(user1) == 0.5
    assert contract.poolOwnership(user2) == 0.5
    assert DAI_token.balanceOf(contract.address) == DAI_ADDED
    assert USDC_token.balanceOf(contract.address) == USDC_ADDED

    # amount > owned (liquidity)
    assert_fail(lambda: contract.removeLiquidity(USDC_token.address, NEW_USER_TWO_BALANCE + 1, DEADLINE, transact={'from': user2}))
    # deadline < block.timestamp
    assert_fail(lambda: contract.removeLiquidity(USDC_token.address, TRANSFERRED_AMOUNT, 1, transact={'from': user2}))
    # amount > token liquidity
    assert_fail(lambda: contract.removeLiquidity(DAI_token.address, DAI_ADDED * TOKEN_PRICE + 1, DEADLINE, transact={'from': user2}))

    # permissions['liquidityRemovingAllowed'] should be True
    assert contract.permissions(b'liquidityRemovingAllowed')
    contract.updatePermission(b'liquidityRemovingAllowed', False, transact={'from': owner})
    assert_fail(lambda: contract.removeLiquidity(DAI_token.address, DAI_ADDED * TOKEN_PRICE, DEADLINE, transact={'from': user2}))
    contract.updatePermission(b'liquidityRemovingAllowed', True, transact={'from': owner})

    # First and second liquidity providers remove their remaining liquidity
    contract.removeLiquidity(DAI_token.address, int(DAI_ADDED * TOKEN_PRICE), DEADLINE, transact={'from': user2})
    contract.removeLiquidity(USDC_token.address, NEW_USER_TWO_BALANCE - int(DAI_ADDED * TOKEN_PRICE), DEADLINE, transact={'from': user2})
    assert contract.poolOwnership(user2) == 0
    assert contract.poolOwnership(user1) == 1
    contract.removeLiquidity(USDC_token.address, NEW_USER_ONE_BALANCE, DEADLINE, transact={'from': user1})
    assert contract.totalSupply() == 0
    assert contract.balanceOf(user1) == 0
    assert contract.balanceOf(user2) == 0
    assert USDC_token.balanceOf(user1) == NEW_USER_ONE_BALANCE / TOKEN_PRICE / 10**(18-6)
    assert DAI_token.balanceOf(user2) == DAI_ADDED
    assert DAI_token.balanceOf(contract.address) == 0
    assert USDC_token.balanceOf(contract.address) == 0

    # Can add liquidity again after all liquidity is divested
    contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user1})
