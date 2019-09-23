from decimal import (
    Decimal, getcontext
)

from tests.constants import (
    DEADLINE
)

def test_proxy_contract(w3, fixed_contract, proxy_contract):
    assert proxy_contract.owner() == w3.eth.defaultAccount
    assert proxy_contract.name() == 'StablecoinswapProxy'
    assert proxy_contract.stablecoinswapAddress() == fixed_contract.address

def test_fees(w3, proxy_contract, assert_fail):
    owner = w3.eth.defaultAccount
    non_owner = w3.eth.accounts[1]
    # initial value
    assert proxy_contract.fee() == Decimal('0.0025')

    assert_fail(lambda: proxy_contract.updateFee(Decimal('0.003'), transact={'from': non_owner}))
    assert_fail(lambda: proxy_contract.updateFee(Decimal('-0.003'), transact={'from': owner}))
    proxy_contract.updateFee(Decimal('0.003'), transact={'from': owner})
    assert proxy_contract.fee() == Decimal('0.003')

def test_exchange_rate(w3, fixed_contract, proxy_contract, GUSD_token, USDC_token):
    getcontext().prec = 20
    # both tokens have price 1.00 USD, total fees of the main contract is 0.3%
    assert fixed_contract.tokenExchangeRateAfterFees(USDC_token.address, GUSD_token.address) == 0.997 * 10**18
    assert proxy_contract.fee() == Decimal('0.0025')
    assert proxy_contract.tokenExchangeRateAfterFees(USDC_token.address, GUSD_token.address) == Decimal('0.997') * Decimal('0.9975') * 10**18

def test_output_amount(w3, fixed_contract, proxy_contract, GUSD_token, USDC_token):
    input_amount = 10
    assert fixed_contract.tokenOutputAmountAfterFees(input_amount * 10**2, GUSD_token.address, USDC_token.address) == input_amount * 10**6 * 0.997
    assert proxy_contract.fee() == Decimal('0.0025')
    assert proxy_contract.tokenOutputAmountAfterFees(input_amount * 10**2, GUSD_token.address, USDC_token.address) == input_amount * 10**6 * 0.997 * 0.9975

def test_ownership(w3, proxy_contract, assert_fail):
    old_owner = w3.eth.defaultAccount
    new_owner = w3.eth.accounts[1]
    assert proxy_contract.owner() == old_owner
    # new owner address can't be empty
    assert_fail(lambda: proxy_contract.transferOwnership(ZERO_ADDR, transact={'from': old_owner}))
    assert proxy_contract.transferOwnership(new_owner, transact={'from': old_owner})
    assert proxy_contract.owner() == new_owner
    # this function should be called by owner
    assert_fail(lambda: proxy_contract.transferOwnership(old_owner, transact={'from': old_owner}))

def test_fee_withdrawal(w3, proxy_contract, assert_fail, GUSD_token):
    GUSD_10 = 10*10**2
    owner = w3.eth.defaultAccount
    non_owner = w3.eth.accounts[1]
    GUSD_token.transfer(proxy_contract.address, GUSD_10, transact={})
    owner_balance_before = GUSD_token.balanceOf(owner)

    assert_fail(lambda: proxy_contract.withdrawFee(GUSD_token.address, GUSD_10, transact={'from': non_owner}))
    assert_fail(lambda: proxy_contract.withdrawFee(GUSD_token.address, GUSD_10 + 1, transact={'from': owner}))

    proxy_contract.withdrawFee(GUSD_token.address, GUSD_10, transact={'from': owner})
    assert GUSD_token.balanceOf(proxy_contract.address) == 0
    assert GUSD_token.balanceOf(owner) == owner_balance_before + GUSD_10

def test_swap(w3, proxy_contract, fixed_contract, fixed_price_oracle, GUSD_token, USDC_token):
    owner = w3.eth.defaultAccount
    proxy_contract.updateFee(Decimal('0.0025'), transact={'from': owner})
    fixed_contract.updateFee('tradeFee', Decimal('0.002'), transact={'from': owner})
    fixed_contract.updateFee('ownerFee', Decimal('0.001'), transact={'from': owner})
    fixed_price_oracle.updateTokenAddress(GUSD_token.address, 0, transact={'from': owner})
    fixed_price_oracle.updateTokenAddress(USDC_token.address, 1, transact={'from': owner})

    user = w3.eth.accounts[1]
    user2 = w3.eth.accounts[2]
    GUSD_100 = 100 * 10**2
    GUSD_token.transfer(user, GUSD_100, transact={})
    GUSD_token.approve(proxy_contract.address, 10**20, transact={'from': user})
    USDC_token.transfer(user2, 200 * 10**6, transact={})
    USDC_token.approve(fixed_contract.address, 10**20, transact={'from': user2})
    fixed_contract.addLiquidity(USDC_token.address, 200 * 10**6, DEADLINE, transact={'from': user2})
    
    assert USDC_token.balanceOf(user) == 0
    assert USDC_token.balanceOf(proxy_contract.address) == 0
    assert GUSD_token.balanceOf(proxy_contract.address) == 0
    assert GUSD_token.balanceOf(fixed_contract.address) == 0
    assert GUSD_token.allowance(proxy_contract.address, fixed_contract.address) == 0
    
    #Сделать своп
    MIN_USDC_AMOUNT = proxy_contract.tokenOutputAmountAfterFees(GUSD_100, GUSD_token.address, USDC_token.address)

    proxy_contract.swapTokens(GUSD_token.address, USDC_token.address, GUSD_100, MIN_USDC_AMOUNT, DEADLINE, transact={'from': user})

    # proxy creates an allowance on first call
    assert GUSD_token.allowance(proxy_contract.address, fixed_contract.address) > 10**30
    # GUSD was spent by the user
    assert GUSD_token.balanceOf(user) == 0
    # a fee was charged by the proxy
    PROXY_FEE = GUSD_100 * 0.0025
    assert GUSD_token.balanceOf(proxy_contract.address) == PROXY_FEE
    # GUSD (after fees) was transferred to the main contract
    assert GUSD_token.balanceOf(fixed_contract.address) == GUSD_100 - PROXY_FEE
    # proxy doesn't charge a fee in output token
    assert USDC_token.balanceOf(proxy_contract.address) == 0
    # correct amount of USDC was sent to the user
    assert USDC_token.balanceOf(user) == MIN_USDC_AMOUNT
    
    # FIXME: test a scenario with low numbers and rounding
