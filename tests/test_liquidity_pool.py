from decimal import (
    Decimal, getcontext
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

def test_add_liquidity(w3, contract, DAI_token, USDC_token, price_oracle, assert_fail):
    owner = w3.eth.accounts[0]
    user = w3.eth.accounts[1]

    DAI_token.transfer(owner, 15 * 10**18, transact={})
    DAI_token.approve(contract.address, 15 * 10**18, transact={'from': owner})
    USDC_token.transfer(user, 15 * 10**6, transact={})
    USDC_token.approve(contract.address, 15 * 10**6, transact={'from': user})

    DAI_PRICE = 1
    USDC_PRICE = 1.2
    price_oracle.updatePrice(DAI_token.address, DAI_PRICE * 10**8, transact={'from': owner})
    price_oracle.updatePrice(USDC_token.address, int(USDC_PRICE * 10**8), transact={'from': owner})
    price_oracle.updateTokenAddress(DAI_token.address, 0, transact={'from': owner})
    price_oracle.updateTokenAddress(USDC_token.address, 1, transact={'from': owner})

    DAI_ADDED = 1 * 10**18
    contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': owner})
    USDC_ADDED = 1 * 10**6
    contract.addLiquidity(USDC_token.address, USDC_ADDED, DEADLINE, transact={'from': user})
    assert contract.totalSupply() == DAI_ADDED * DAI_PRICE + USDC_ADDED * USDC_PRICE * 10**(18-6)
    assert contract.balanceOf(owner) == DAI_ADDED * DAI_PRICE
    assert contract.balanceOf(user) == USDC_ADDED * 10**(18-6) * USDC_PRICE
    assert price_oracle.poolSize(contract.address) == DAI_ADDED * DAI_PRICE + USDC_ADDED * USDC_PRICE * 10**(18-6)

    NEW_DAI_PRICE = 1.5
    price_oracle.updatePrice(DAI_token.address, int(NEW_DAI_PRICE * 10**8), transact={'from': owner})
    assert contract.totalSupply() == DAI_ADDED * DAI_PRICE + USDC_ADDED * USDC_PRICE * 10**(18-6)
    assert price_oracle.poolSize(contract.address) == DAI_ADDED * NEW_DAI_PRICE + USDC_ADDED * USDC_PRICE * 10**(18-6)

def test_liquidity_pool(w3, contract, DAI_token, USDC_token, price_oracle, assert_fail):
    owner = w3.eth.accounts[0]
    user1 = w3.eth.accounts[1]
    user2 = w3.eth.accounts[2]
    TOKEN_PRICE = 1.01
    INT_TOKEN_PRICE =  int(TOKEN_PRICE * 10**8)
    DAI_token.transfer(user1, 25*10**18, transact={})
    DAI_token.approve(contract.address, 25*10**18, transact={'from': user1})
    DAI_ADDED = 10 * 10**18 # 10 DAI
    price_oracle.updatePrice(DAI_token.address, INT_TOKEN_PRICE, transact={'from': owner})
    price_oracle.updateTokenAddress(DAI_token.address, 0, transact={'from': owner})

    # permissions['liquidityAddingAllowed'] should be True
    assert contract.permissions(b'liquidityAddingAllowed')
    contract.updatePermission(b'liquidityAddingAllowed', False, transact={'from': owner})
    assert_fail(lambda: contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user1}))
    contract.updatePermission(b'liquidityAddingAllowed', True, transact={'from': owner})
    contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user1})

    USDC_token.transfer(user2, 42*10**6, transact={})
    USDC_token.approve(contract.address, 42*10**6, transact={'from': user2})
    USDC_ADDED = 30 * 10**6 # 30 USDC
    price_oracle.updatePrice(USDC_token.address, INT_TOKEN_PRICE, transact={'from': owner})
    price_oracle.updateTokenAddress(USDC_token.address, 1, transact={'from': owner})
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
    TOTAL_SUPPLY_BEFORE = (DAI_ADDED + USDC_ADDED * 10**(18-6)) * TOKEN_PRICE
    assert contract.totalSupply() == TOTAL_SUPPLY_BEFORE
    # At this step 1 contract token (10**18 base units) == 1 USD
    POOL_SIZE_BEFORE = TOTAL_SUPPLY_BEFORE
    assert price_oracle.poolSize(contract.address) == POOL_SIZE_BEFORE
    assert contract.balanceOf(owner) == 0

    # second provider removes liquidity in DAI
    amount_to_remove = int(DAI_ADDED * TOKEN_PRICE * TOTAL_SUPPLY_BEFORE / POOL_SIZE_BEFORE)
    owner_fee = int(amount_to_remove * 0.001)
    new_total_supply = TOTAL_SUPPLY_BEFORE - amount_to_remove + owner_fee
    new_pool_size = POOL_SIZE_BEFORE - int(amount_to_remove * 0.997)
    contract.removeLiquidity(DAI_token.address, amount_to_remove, DEADLINE, transact={'from': user2})
    assert contract.balanceOf(owner) == owner_fee
    assert DAI_token.balanceOf(user2) == int(DAI_ADDED * 0.997)
    assert contract.totalSupply() == new_total_supply
    assert price_oracle.poolSize(contract.address) == new_pool_size
    assert DAI_token.balanceOf(contract.address) == int(DAI_ADDED * 0.003)

    # second provider removes remaining liquidity in USDC
    amount_to_remove = NEW_USER_TWO_BALANCE - amount_to_remove
    assert contract.balanceOf(user2) == amount_to_remove
    new_owner_fee = int(amount_to_remove * 0.001)
    # amount_to_transfer is how many USDC user will receive
    amount_to_transfer = int(amount_to_remove * 0.997 * new_pool_size / new_total_supply / TOKEN_PRICE / 10**(18-6))
    owner_fee += new_owner_fee
    new_total_supply = NEW_USER_ONE_BALANCE + owner_fee
    pool_size_change = int(amount_to_transfer * TOKEN_PRICE * 10**(18-6))
    new_pool_size -= pool_size_change
    contract.removeLiquidity(USDC_token.address, amount_to_remove, DEADLINE, transact={'from': user2})
    assert contract.totalSupply() == new_total_supply
    assert contract.balanceOf(user2) == 0
    assert contract.balanceOf(owner) == owner_fee
    assert USDC_token.balanceOf(user2) == 12*10**6 + amount_to_transfer
    usdc_balance = USDC_ADDED - amount_to_transfer
    assert USDC_token.balanceOf(contract.address) == usdc_balance
    assert price_oracle.poolSize(contract.address) == new_pool_size

    # first provider removes liquidity in USDC
    assert contract.balanceOf(user1) == NEW_USER_ONE_BALANCE
    new_owner_fee = int(NEW_USER_ONE_BALANCE * 0.001)
    amount_to_transfer = int(NEW_USER_ONE_BALANCE * new_pool_size / new_total_supply * 0.997)
    contract.removeLiquidity(USDC_token.address, NEW_USER_ONE_BALANCE, DEADLINE, transact={'from': user1})
    owner_fee += new_owner_fee
    usdc_balance -= int(amount_to_transfer / TOKEN_PRICE / 10**(18-6))

    pool_size_change = int(Decimal(int(amount_to_transfer / TOKEN_PRICE / 10**(18-6))) * Decimal(TOKEN_PRICE) * Decimal(10**(18-6)))
    getcontext().prec = 12
    new_pool_size = int(Decimal(new_pool_size) - Decimal(pool_size_change))

    # check contract balances and pool size
    assert contract.totalSupply() == owner_fee
    assert price_oracle.poolSize(contract.address) == new_pool_size
    assert contract.balanceOf(user1) == 0
    assert contract.balanceOf(user2) == 0
    assert contract.balanceOf(owner) == owner_fee
    assert USDC_token.balanceOf(user1) == int(amount_to_transfer / TOKEN_PRICE / 10**(18-6))
    assert USDC_token.balanceOf(contract.address) == usdc_balance

    # owner removes remaining liquidity
    assert DAI_token.balanceOf(contract.address) == DAI_ADDED * 0.003
    new_total_liquidity = owner_fee
    getcontext().prec = 18
    amount_to_remove = int(Decimal(DAI_ADDED) * Decimal(0.003) * Decimal(TOKEN_PRICE) * Decimal(new_total_liquidity) / Decimal(new_pool_size))
    contract.removeLiquidity(DAI_token.address, amount_to_remove, DEADLINE, transact={'from': owner})
    assert DAI_token.balanceOf(contract.address) == 0
    amount_to_remove = new_total_liquidity - amount_to_remove
    contract.removeLiquidity(USDC_token.address, amount_to_remove, DEADLINE, transact={'from': owner})
    assert USDC_token.balanceOf(contract.address) == 0
    assert contract.balanceOf(owner) == 0

    # Can add liquidity again after all liquidity is divested
    contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user1})
