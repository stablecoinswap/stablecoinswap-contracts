from decimal import Decimal

def test_exchange_rate(w3, contract, price_oracle, DAI_token, USDC_token):
  owner = w3.eth.defaultAccount
  user = w3.eth.accounts[1]

  # initial fee values
  assert contract.fees('tradeFee') == Decimal('0.002')
  assert contract.fees('ownerFee') == Decimal('0.001')

  # set token prices
  price_oracle.updatePrice(DAI_token.address, 101 * 10**6, transact={'from': owner}) # $1,01
  price_oracle.updatePrice(USDC_token.address, 99 * 10**6 * 10**12, transact={'from': owner}) # $0,99
  price_oracle.updateTokenAddress(DAI_token.address, 0, transact={'from': owner})
  price_oracle.updateTokenAddress(USDC_token.address, 1, transact={'from': owner})

  assert price_oracle.normalized_token_prices(DAI_token.address) == 101 * 10**6
  assert price_oracle.normalized_token_prices(USDC_token.address) == 99 * 10**18

  # DAI -> USDC: 1.017141
  assert contract.tokenExchangeRateAfterFees(DAI_token.address, USDC_token.address) == 1017141
  # USDC -> DAI: 0.977257
  assert contract.tokenExchangeRateAfterFees(USDC_token.address, DAI_token.address) == 977257425742574257

def test_output_amount(w3, contract, price_oracle, DAI_token, USDC_token):
  owner = w3.eth.defaultAccount
  user = w3.eth.accounts[1]

  # initial fee values
  assert contract.fees('tradeFee') == Decimal('0.002')
  assert contract.fees('ownerFee') == Decimal('0.001')

  # set token prices
  price_oracle.updatePrice(DAI_token.address, 101 * 10**6, transact={'from': owner}) # $1,01
  price_oracle.updatePrice(USDC_token.address, 99 * 10**6 * 10**12, transact={'from': owner}) # $0,99
  price_oracle.updateTokenAddress(DAI_token.address, 0, transact={'from': owner})
  price_oracle.updateTokenAddress(USDC_token.address, 1, transact={'from': owner})

  # DAI -> USDC
  input_amount = int(1.25 * 10**18)
  expected_output_amount = int(1.25 * 1017141)
  assert contract.tokenOutputAmountAfterFees(input_amount, DAI_token.address, USDC_token.address) == expected_output_amount

  # USDC -> DAI
  input_amount = int(2 * 10**6)
  expected_output_amount = int(2 * 977257425742574257)
  assert contract.tokenOutputAmountAfterFees(input_amount, USDC_token.address, DAI_token.address) == expected_output_amount
