from decimal import (
    Decimal, getcontext
)
from tests.constants import (EXCHANGE_RATE_MULTIPLIER_POW)

def test_exchange_rate(w3, contract, price_oracle, DAI_token, GUSD_token, USDC_token):
  owner = w3.eth.defaultAccount

  # initial fee values
  assert contract.fees('tradeFee') == Decimal('0.002')
  assert contract.fees('ownerFee') == Decimal('0.001')

  # set token prices
  price_oracle.updatePrice(DAI_token.address, 101 * 10**6, transact={'from': owner}) # 1.01
  price_oracle.updatePrice(USDC_token.address, 99 * 10**6 * 10**12, transact={'from': owner}) # 0.99
  price_oracle.updatePrice(GUSD_token.address, 125 * 10**6 * 10**16, transact={'from': owner}) # 1.25
  price_oracle.updateTokenAddress(DAI_token.address, 0, transact={'from': owner})
  price_oracle.updateTokenAddress(USDC_token.address, 1, transact={'from': owner})
  price_oracle.updateTokenAddress(GUSD_token.address, 2, transact={'from': owner})

  assert price_oracle.normalized_token_prices(DAI_token.address) == 101 * 10**6
  assert price_oracle.normalized_token_prices(USDC_token.address) == 99 * 10**18
  assert price_oracle.normalized_token_prices(GUSD_token.address) == 125 * 10**22

  # DAI -> USDC: 1.0171414141
  # we have 10 decimals here because the number of decimals is:
  # EXCHANGE_RATE_MULTIPLIER_POW - input_token.decimals + output_token.decimals
  # (22 - 18 + 6)
  assert contract.tokenExchangeRateAfterFees(DAI_token.address, USDC_token.address) == 10171414141
  # USDC -> DAI: 0.9772574257425742574257425742574257
  assert contract.tokenExchangeRateAfterFees(USDC_token.address, DAI_token.address) == 9772574257425742574257425742574257
  # DAI -> GUSD: 0.805576
  assert contract.tokenExchangeRateAfterFees(DAI_token.address, GUSD_token.address) == 805576
  # GUSD -> DAI: 1.23391089108910891089108910891089108910
  assert contract.tokenExchangeRateAfterFees(GUSD_token.address, DAI_token.address) == 123391089108910891089108910891089108910
  # USDC -> GUSD: 0.789624
  assert contract.tokenExchangeRateAfterFees(USDC_token.address, GUSD_token.address) == 789624000000000000
  # GUSD -> USDC: 1.25883838383838383838383838
  assert contract.tokenExchangeRateAfterFees(GUSD_token.address, USDC_token.address) == 125883838383838383838383838

def test_output_amount(w3, contract, price_oracle, DAI_token, GUSD_token, USDC_token):
  owner = w3.eth.defaultAccount
  getcontext().prec = 36
  # initial fee values
  assert contract.fees('tradeFee') == Decimal('0.002')
  assert contract.fees('ownerFee') == Decimal('0.001')

  # set token prices
  price_oracle.updatePrice(DAI_token.address, 101 * 10**6, transact={'from': owner}) # 1.01
  price_oracle.updatePrice(USDC_token.address, 99 * 10**6 * 10**12, transact={'from': owner}) # 0.99
  price_oracle.updatePrice(GUSD_token.address, 125 * 10**6 * 10**16, transact={'from': owner}) # 1.25
  price_oracle.updateTokenAddress(DAI_token.address, 0, transact={'from': owner})
  price_oracle.updateTokenAddress(USDC_token.address, 1, transact={'from': owner})
  price_oracle.updateTokenAddress(GUSD_token.address, 2, transact={'from': owner})

  # DAI -> USDC
  input_amount = int(1.25 * 10**18)
  expected_output_amount = int(1.25 * 1017141)
  assert contract.tokenOutputAmountAfterFees(input_amount, DAI_token.address, USDC_token.address) == expected_output_amount

  # USDC -> DAI
  input_amount = int(2 * 10**6)
  expected_output_amount = 2 * int(Decimal('9772574257425742574257425742574257') / Decimal(10)**Decimal(EXCHANGE_RATE_MULTIPLIER_POW-6))
  assert contract.tokenOutputAmountAfterFees(input_amount, USDC_token.address, DAI_token.address) == expected_output_amount

  # DAI -> GUSD
  input_amount = int(0.7 * 10**18)
  expected_output_amount = int(0.7 * 805576 / 10**(EXCHANGE_RATE_MULTIPLIER_POW-18))
  assert contract.tokenOutputAmountAfterFees(input_amount, DAI_token.address, GUSD_token.address) == expected_output_amount

  # GUSD -> DAI
  input_amount = int(0.1 * 10**2)
  expected_output_amount = int(Decimal('0.1') * Decimal('123391089108910891089108910891089108910') / Decimal(10)**Decimal(EXCHANGE_RATE_MULTIPLIER_POW-2))
  assert contract.tokenOutputAmountAfterFees(input_amount, GUSD_token.address, DAI_token.address) == expected_output_amount

  # USDC -> GUSD
  input_amount = int(1.6 * 10**6)
  expected_output_amount = int(1.6 * 789624000000000000 / 10**(EXCHANGE_RATE_MULTIPLIER_POW-6))
  assert contract.tokenOutputAmountAfterFees(input_amount, USDC_token.address, GUSD_token.address) == expected_output_amount

  # GUSD -> USDC
  input_amount = int(0.99 * 10**2)
  expected_output_amount = int(Decimal('0.99') * Decimal('125883838383838383838383838') / Decimal(10)**Decimal(EXCHANGE_RATE_MULTIPLIER_POW-2))
  assert contract.tokenOutputAmountAfterFees(input_amount, GUSD_token.address, USDC_token.address) == expected_output_amount
