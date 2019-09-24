from decimal import (
    Decimal, getcontext
)

from tests.constants import (
    DEADLINE
)
import math

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
    input_amount = 100
    assert fixed_contract.tokenOutputAmountAfterFees(input_amount * 10**2, GUSD_token.address, USDC_token.address) == input_amount * 10**6 * 0.997
    assert proxy_contract.fee() == Decimal('0.0025')
    assert proxy_contract.tokenOutputAmountAfterFees(input_amount * 10**2, GUSD_token.address, USDC_token.address) == input_amount * 10**6 * 0.997 * 0.9975
    # it rounds an amount down
    proxy_fee = math.ceil(10**2 * 0.0025)
    amount_after_fees = (10**2 - proxy_fee) * 0.997 * 10**(6-2)
    assert proxy_contract.tokenOutputAmountAfterFees(1*10**2, GUSD_token.address, USDC_token.address) == amount_after_fees

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
