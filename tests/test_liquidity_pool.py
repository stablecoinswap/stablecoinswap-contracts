from decimal import (
    Decimal, getcontext
)

from math import (
    floor, ceil
)

from tests.constants import (
    DEADLINE, MAX_GAS_USED
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

def test_add_liquidity(w3, contract, DAI_token, GUSD_token, USDC_token, price_oracle, assert_fail):
    owner = w3.eth.accounts[0]
    user = w3.eth.accounts[1]

    DAI_token.transfer(owner, 15 * 10**18, transact={})
    DAI_token.approve(contract.address, 15 * 10**18, transact={'from': owner})
    GUSD_token.transfer(user, 15 * 10**2, transact={})
    GUSD_token.approve(contract.address, 15 * 10**2, transact={'from': user})
    USDC_token.transfer(user, 15 * 10**6, transact={})
    USDC_token.approve(contract.address, 15 * 10**6, transact={'from': user})

    DAI_PRICE = 1
    GUSD_PRICE = Decimal('0.98')
    USDC_PRICE = Decimal('1.2')
    price_oracle.updatePrice(DAI_token.address, DAI_PRICE * 10**8, transact={'from': owner})
    price_oracle.updatePrice(GUSD_token.address, int(GUSD_PRICE * 10**8 * 10**16), transact={'from': owner})
    price_oracle.updatePrice(USDC_token.address, int(USDC_PRICE * 10**8 * 10**12), transact={'from': owner})
    price_oracle.updateTokenAddress(DAI_token.address, 0, transact={'from': owner})
    price_oracle.updateTokenAddress(USDC_token.address, 1, transact={'from': owner})
    price_oracle.updateTokenAddress(GUSD_token.address, 2, transact={'from': owner})

    DAI_ADDED = 1 * 10**18
    contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': owner})
    USDC_ADDED = 1 * 10**6
    contract.addLiquidity(USDC_token.address, USDC_ADDED, DEADLINE, transact={'from': user})
    assert contract.totalSupply() == DAI_ADDED * DAI_PRICE + USDC_ADDED * USDC_PRICE * 10**(18-6)
    assert contract.balanceOf(owner) == DAI_ADDED * DAI_PRICE
    assert contract.balanceOf(user) == USDC_ADDED * 10**(18-6) * USDC_PRICE
    assert price_oracle.poolSize(contract.address) == DAI_ADDED * DAI_PRICE + USDC_ADDED * USDC_PRICE * 10**(18-6)

    GUSD_ADDED = 1 * 10**2
    contract.addLiquidity(GUSD_token.address, GUSD_ADDED, DEADLINE, transact={'from': user})
    assert contract.totalSupply() == DAI_ADDED * DAI_PRICE + USDC_ADDED * USDC_PRICE * 10**(18-6) + GUSD_ADDED * GUSD_PRICE * 10**(18-2)
    assert contract.balanceOf(owner) == DAI_ADDED * DAI_PRICE
    assert contract.balanceOf(user) == USDC_ADDED * 10**(18-6) * USDC_PRICE + GUSD_ADDED * 10**(18-2) * GUSD_PRICE
    assert price_oracle.poolSize(contract.address) == DAI_ADDED * DAI_PRICE + USDC_ADDED * USDC_PRICE * 10**(18-6) + GUSD_ADDED * GUSD_PRICE * 10**(18-2)

    NEW_DAI_PRICE = 1.5
    price_oracle.updatePrice(DAI_token.address, int(NEW_DAI_PRICE * 10**8), transact={'from': owner})
    assert contract.totalSupply() == DAI_ADDED * DAI_PRICE + USDC_ADDED * USDC_PRICE * 10**(18-6) + GUSD_ADDED * GUSD_PRICE * 10**(18-2)
    assert price_oracle.poolSize(contract.address) == DAI_ADDED * NEW_DAI_PRICE + int(USDC_ADDED * USDC_PRICE * 10**(18-6)) + int(GUSD_ADDED * GUSD_PRICE * 10**(18-2))

    # following asserts are necessary to test a rounding
    # add 1 DAI at the lowest level of precision (10^(-18) DAI token)
    contract.addLiquidity(DAI_token.address, 1, DEADLINE, transact={'from': owner})
    # it will not increase totalSupply because 10^(-18) DAI costs
    # less than 10^(-18) stablecoinswap contract token
    assert contract.totalSupply() == DAI_ADDED * DAI_PRICE + USDC_ADDED * USDC_PRICE * 10**(18-6) + GUSD_ADDED * GUSD_PRICE * 10**(18-2)
    DAI_ADDED = DAI_ADDED + 1 # 10^18 + 1

    # tests for price values (price multiplier is 10**8):
    # the absolute minimum + 1 (at the lowest level of precision) and the maximum - 1
    DAI_MIN_PRICE = 0.01000001
    price_oracle.updatePrice(DAI_token.address, int(DAI_MIN_PRICE * 10**8), transact={'from': owner})
    assert price_oracle.poolSize(contract.address) == DAI_ADDED * DAI_MIN_PRICE + int(USDC_ADDED * USDC_PRICE * 10**(18-6)) + int(GUSD_ADDED * GUSD_PRICE * 10**(18-2))

    DAI_MAX_PRICE = Decimal('99.99999999')
    price_oracle.updatePrice(DAI_token.address, int(DAI_MAX_PRICE * 10**8), transact={'from': owner})

    assert price_oracle.poolSize(contract.address) == floor(Decimal(DAI_ADDED) * Decimal(DAI_MAX_PRICE)) + Decimal(USDC_ADDED) * Decimal(USDC_PRICE) * Decimal(10**(18-6)) + Decimal(GUSD_ADDED) * Decimal(GUSD_PRICE) * Decimal(10**(18-2))

def test_liquidity_pool(w3, contract, DAI_token, GUSD_token, price_oracle, assert_fail):
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
    assert contract.permissions('liquidityAddingAllowed')
    contract.updatePermission('liquidityAddingAllowed', False, transact={'from': owner})
    assert_fail(lambda: contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user1}))
    contract.updatePermission('liquidityAddingAllowed', True, transact={'from': owner})
    contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user1})

    GUSD_token.transfer(user2, 42*10**2, transact={})
    GUSD_token.approve(contract.address, 42*10**2, transact={'from': user2})
    GUSD_ADDED = 30 * 10**2 # 30 GUSD
    price_oracle.updatePrice(GUSD_token.address, INT_TOKEN_PRICE * 10**16, transact={'from': owner})
    price_oracle.updateTokenAddress(GUSD_token.address, 1, transact={'from': owner})
    contract.addLiquidity(GUSD_token.address, GUSD_ADDED, DEADLINE, transact={'from': user2})

    assert contract.totalSupply() == (DAI_ADDED + GUSD_ADDED * 10**(18-2)) * TOKEN_PRICE
    assert contract.balanceOf(user1) == DAI_ADDED * TOKEN_PRICE
    assert contract.balanceOf(user2) == GUSD_ADDED * 10**(18-2) * TOKEN_PRICE
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
    NEW_USER_TWO_BALANCE = int(GUSD_ADDED * 10**(18-2) * TOKEN_PRICE) - TRANSFERRED_AMOUNT
    assert contract.balanceOf(user1) == NEW_USER_ONE_BALANCE
    assert contract.balanceOf(user2) == NEW_USER_TWO_BALANCE
    assert contract.poolOwnership(user1) == 0.5
    assert contract.poolOwnership(user2) == 0.5
    assert DAI_token.balanceOf(contract.address) == DAI_ADDED
    assert GUSD_token.balanceOf(contract.address) == GUSD_ADDED

    # amount > owned (liquidity)
    assert_fail(lambda: contract.removeLiquidity(GUSD_token.address, NEW_USER_TWO_BALANCE + 1, 0, DEADLINE, transact={'from': user2}))
    # deadline < block.timestamp
    assert_fail(lambda: contract.removeLiquidity(GUSD_token.address, TRANSFERRED_AMOUNT, 0, 1, transact={'from': user2}))
    # amount > token liquidity
    assert_fail(lambda: contract.removeLiquidity(DAI_token.address, DAI_ADDED * TOKEN_PRICE + 1, 0, DEADLINE, transact={'from': user2}))

    # First and second liquidity providers remove their remaining liquidity
    TOTAL_SUPPLY_BEFORE = (DAI_ADDED + GUSD_ADDED * 10**(18-2)) * TOKEN_PRICE
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
    # amount < erc20_min_output_amount
    assert_fail(lambda: contract.removeLiquidity(DAI_token.address, amount_to_remove, int(DAI_ADDED * 0.997) + 1, DEADLINE, transact={'from': user2}))

    contract.removeLiquidity(DAI_token.address, amount_to_remove, int(DAI_ADDED * 0.997), DEADLINE, transact={'from': user2})
    assert contract.balanceOf(owner) == owner_fee
    assert DAI_token.balanceOf(user2) == int(DAI_ADDED * 0.997)
    assert contract.totalSupply() == new_total_supply
    assert price_oracle.poolSize(contract.address) == new_pool_size
    assert DAI_token.balanceOf(contract.address) == int(DAI_ADDED * 0.003)

    # second provider removes remaining liquidity in GUSD
    amount_to_remove = NEW_USER_TWO_BALANCE - amount_to_remove
    assert contract.balanceOf(user2) == amount_to_remove
    new_owner_fee = int(amount_to_remove * 0.001)
    # amount_to_transfer is how many GUSD user will receive
    amount_to_transfer = int(amount_to_remove * 0.997 * new_pool_size / new_total_supply / TOKEN_PRICE / 10**(18-2))
    owner_fee += new_owner_fee
    new_total_supply = NEW_USER_ONE_BALANCE + owner_fee
    pool_size_change = int(amount_to_transfer * TOKEN_PRICE * 10**(18-2))
    new_pool_size -= pool_size_change
    contract.removeLiquidity(GUSD_token.address, amount_to_remove, amount_to_transfer, DEADLINE, transact={'from': user2})
    assert contract.totalSupply() == new_total_supply
    assert contract.balanceOf(user2) == 0
    assert contract.balanceOf(owner) == owner_fee
    assert GUSD_token.balanceOf(user2) == 12*10**2 + amount_to_transfer
    gusd_balance = GUSD_ADDED - amount_to_transfer
    assert GUSD_token.balanceOf(contract.address) == gusd_balance
    assert price_oracle.poolSize(contract.address) == new_pool_size

    # first provider removes liquidity in GUSD
    assert contract.balanceOf(user1) == NEW_USER_ONE_BALANCE
    new_owner_fee = int(NEW_USER_ONE_BALANCE * 0.001)
    amount_to_transfer = int(NEW_USER_ONE_BALANCE * new_pool_size / new_total_supply * 0.997)
    contract.removeLiquidity(GUSD_token.address, NEW_USER_ONE_BALANCE, int(amount_to_transfer / TOKEN_PRICE / 10**(18-2)), DEADLINE, transact={'from': user1})
    owner_fee += new_owner_fee
    gusd_balance -= int(amount_to_transfer / TOKEN_PRICE / 10**(18-2))

    pool_size_change = int(Decimal(int(amount_to_transfer / TOKEN_PRICE / 10**(18-2))) * Decimal(TOKEN_PRICE) * Decimal(10**(18-2)))
    getcontext().prec = 12
    new_pool_size = int(Decimal(new_pool_size) - Decimal(pool_size_change))

    # check contract balances and pool size
    assert contract.totalSupply() == owner_fee
    assert price_oracle.poolSize(contract.address) == new_pool_size
    assert contract.balanceOf(user1) == 0
    assert contract.balanceOf(user2) == 0
    assert contract.balanceOf(owner) == owner_fee
    assert GUSD_token.balanceOf(user1) == int(amount_to_transfer / TOKEN_PRICE / 10**(18-2))
    assert GUSD_token.balanceOf(contract.address) == gusd_balance

    # owner removes remaining liquidity
    assert DAI_token.balanceOf(contract.address) == DAI_ADDED * 0.003
    new_total_liquidity = owner_fee
    getcontext().prec = 17
    amount_to_remove = int(Decimal(DAI_ADDED) * Decimal('0.003') * Decimal(TOKEN_PRICE) * Decimal(new_total_liquidity) / Decimal(new_pool_size))
    contract.removeLiquidity(DAI_token.address, amount_to_remove, amount_to_remove, DEADLINE, transact={'from': owner})
    assert DAI_token.balanceOf(contract.address) == 0
    amount_to_remove = new_total_liquidity - amount_to_remove
    contract.removeLiquidity(GUSD_token.address, amount_to_remove, int(amount_to_remove / TOKEN_PRICE / 10**(18-2)), DEADLINE, transact={'from': owner})
    assert GUSD_token.balanceOf(contract.address) == 0
    assert contract.balanceOf(owner) == 0

    # Can add liquidity again after all liquidity is divested
    contract.addLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': user1})

def test_fees(w3, contract, DAI_token, GUSD_token, price_oracle, assert_fail):
    getcontext().prec = 28
    owner = w3.eth.accounts[0]
    user_dai = w3.eth.accounts[1]
    user_gusd = w3.eth.accounts[2]
    TOKEN_PRICE = Decimal('0.99999999')

    # One use adds 10 DAI
    DAI_token.transfer(user_dai, 25*10**18, transact={})
    DAI_token.approve(contract.address, 25*10**18, transact={'from': user_dai})
    DAI_10 = 10 * 10**18 # 10 DAI
    price_oracle.updatePrice(DAI_token.address, int(TOKEN_PRICE * 10**8), transact={'from': owner})
    price_oracle.updateTokenAddress(DAI_token.address, 0, transact={'from': owner})
    tx_hash = contract.addLiquidity(DAI_token.address, DAI_10, DEADLINE, transact={'from': user_dai})
    transaction = w3.eth.getTransactionReceipt(tx_hash)
    assert transaction['gasUsed'] < MAX_GAS_USED

    # Another user adds 15 GUSD
    GUSD_token.transfer(user_gusd, 42*10**2, transact={})
    GUSD_token.approve(contract.address, 42*10**2, transact={'from': user_gusd})
    GUSD_15 = 15 * 10**2 # 15 GUSD
    price_oracle.updatePrice(GUSD_token.address, int(TOKEN_PRICE * 10**8 * 10**16), transact={'from': owner})
    price_oracle.updateTokenAddress(GUSD_token.address, 1, transact={'from': owner})

    tx_hash = contract.addLiquidity(GUSD_token.address, GUSD_15, DEADLINE, transact={'from': user_gusd})
    transaction = w3.eth.getTransactionReceipt(tx_hash)
    assert transaction['gasUsed'] < MAX_GAS_USED

    # 10 DAI + 15 GUSD total, both at the same price
    TOTAL_SUPPLY_BEFORE = Decimal(25) * Decimal(10**18) * TOKEN_PRICE
    assert contract.totalSupply() == TOTAL_SUPPLY_BEFORE
    assert contract.balanceOf(user_dai) == DAI_10 * TOKEN_PRICE
    assert contract.balanceOf(user_gusd) == GUSD_15 * 10**(18-2) * TOKEN_PRICE
    assert contract.poolOwnership(user_dai) == Decimal('0.4')
    assert contract.poolOwnership(user_gusd) == Decimal('0.6')

    # set fees 0.2% and 0.001% (min fee value)
    contract.updateFee('tradeFee', Decimal('0.002'), transact={'from': owner})
    contract.updateFee('ownerFee', Decimal('0.00001'), transact={'from': owner})
    TOTAL_FEE_PERCENTAGE = Decimal('0.00201')

    # At this step 1 contract token (10**18 base units) == 1 USD
    POOL_SIZE_BEFORE = TOTAL_SUPPLY_BEFORE
    assert price_oracle.poolSize(contract.address) == POOL_SIZE_BEFORE

    # can't remove 0.01 GUSD -> amount to receive will be equal to 0
    assert_fail(lambda: contract.removeLiquidity(GUSD_token.address, ceil(Decimal('0.01') * 10**18 * TOKEN_PRICE), 1, DEADLINE, transact={'from': user_dai}))

    # one user removes 0.02 GUSD
    gusd_to_remove = Decimal('0.02')
    amount_to_remove = ceil(gusd_to_remove * 10**18 * TOKEN_PRICE)
    owner_fee = int(amount_to_remove * 0.00001)
    gusd_received = int(gusd_to_remove * 10**2 * (Decimal(1) - TOTAL_FEE_PERCENTAGE))
    new_total_supply = TOTAL_SUPPLY_BEFORE - amount_to_remove + owner_fee
    new_pool_size = POOL_SIZE_BEFORE - int(gusd_received * 10**(18-2) * TOKEN_PRICE)

    tx_hash = contract.removeLiquidity(GUSD_token.address, amount_to_remove, 1, DEADLINE, transact={'from': user_dai})
    transaction = w3.eth.getTransactionReceipt(tx_hash)
    assert transaction['gasUsed'] < MAX_GAS_USED

    assert contract.totalSupply() == new_total_supply
    assert price_oracle.poolSize(contract.address) == new_pool_size
    assert GUSD_token.balanceOf(user_dai) == gusd_received
    assert contract.balanceOf(owner) == owner_fee
    owner_balance = owner_fee

    # another user removes 0.001 DAI
    dai_to_remove = Decimal('0.001')
    amount_to_remove = ceil(dai_to_remove * 10**18 * TOKEN_PRICE * new_total_supply / new_pool_size)
    owner_fee = int(amount_to_remove * 0.00001)
    owner_balance += owner_fee
    dai_received = int(dai_to_remove * 10**18 * (Decimal(1) - TOTAL_FEE_PERCENTAGE))
    new_total_supply = new_total_supply - amount_to_remove + owner_fee
    new_pool_size = new_pool_size - int(dai_received * TOKEN_PRICE)

    contract.removeLiquidity(DAI_token.address, amount_to_remove, 1, DEADLINE, transact={'from': user_gusd})

    assert contract.totalSupply() == new_total_supply
    assert price_oracle.poolSize(contract.address) == new_pool_size
    assert contract.balanceOf(owner) == owner_balance
    assert DAI_token.balanceOf(user_gusd) == dai_received
