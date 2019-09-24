from decimal import (
    Decimal, getcontext
)

from tests.constants import (
    DEADLINE
)

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

def test_swap_rounding(w3, proxy_contract, fixed_contract, fixed_price_oracle, GUSD_token, USDC_token):
    owner = w3.eth.defaultAccount
    proxy_contract.updateFee(Decimal('0.0025'), transact={'from': owner})
    fixed_contract.updateFee('tradeFee', Decimal('0.002'), transact={'from': owner})
    fixed_contract.updateFee('ownerFee', Decimal('0.001'), transact={'from': owner})
    fixed_price_oracle.updateTokenAddress(GUSD_token.address, 0, transact={'from': owner})
    fixed_price_oracle.updateTokenAddress(USDC_token.address, 1, transact={'from': owner})

    user = w3.eth.accounts[1]
    user2 = w3.eth.accounts[2]
    GUSD_1 = 10**2
    GUSD_token.transfer(user, GUSD_1, transact={})
    GUSD_token.approve(proxy_contract.address, 10**20, transact={'from': user})
    USDC_token.transfer(user2, 200 * 10**6, transact={})
    USDC_token.approve(fixed_contract.address, 10**20, transact={'from': user2})
    fixed_contract.addLiquidity(USDC_token.address, 200 * 10**6, DEADLINE, transact={'from': user2})

    assert USDC_token.balanceOf(user) == 0
    assert GUSD_token.balanceOf(proxy_contract.address) == 0
    assert GUSD_token.balanceOf(fixed_contract.address) == 0

    MIN_USDC_AMOUNT = proxy_contract.tokenOutputAmountAfterFees(GUSD_1, GUSD_token.address, USDC_token.address)

    proxy_contract.swapTokens(GUSD_token.address, USDC_token.address, GUSD_1, MIN_USDC_AMOUNT, DEADLINE, transact={'from': user})

    # GUSD was spent by the user
    assert GUSD_token.balanceOf(user) == 0
    # it rounds a fee up
    PROXY_FEE = 1
    assert GUSD_token.balanceOf(proxy_contract.address) == PROXY_FEE
    # GUSD (after fees) was transferred to the main contract
    assert GUSD_token.balanceOf(fixed_contract.address) == GUSD_1 - PROXY_FEE
    # correct amount of USDC was sent to the user
    assert USDC_token.balanceOf(user) == MIN_USDC_AMOUNT
