from decimal import (
    Decimal,
)

from tests.constants import (
    DEADLINE
)

DAI_PRICE = 1010000000000000000 #1.01*10**18
MAX_DAI_PRICE = 1050000000000000000
MIN_DAI_PRICE = 950000000000000000

def test_price_oracle(w3, DAI_token, USDC_token, dai_oracle, fixed_price_oracle, assert_fail):
  owner = w3.eth.accounts[0]
  user = w3.eth.accounts[1]

  assert fixed_price_oracle.name() == 'PriceOracle'
  assert fixed_price_oracle.supportedTokens(0) == DAI_token.address
  assert fixed_price_oracle.supportedTokens(1) == None

  # only owner can update token address
  assert_fail(lambda: fixed_price_oracle.updateTokenAddress(USDC_token.address, 1, transact={'from': user}))
  fixed_price_oracle.updateTokenAddress(USDC_token.address, 1, transact={'from': owner})

  dai_oracle.updatePrice(10**18, transact={'from': owner})

  assert fixed_price_oracle.normalized_token_prices(DAI_token.address) == 100000000
  assert fixed_price_oracle.normalized_token_prices(USDC_token.address) == 100000000000000000000
  dai_oracle.updatePrice(DAI_PRICE, transact={'from': owner})
  assert fixed_price_oracle.normalized_token_prices(DAI_token.address) == 101000000

  # test min and max dai prices
  dai_oracle.updatePrice(MAX_DAI_PRICE, transact={'from': owner})
  assert fixed_price_oracle.normalized_token_prices(DAI_token.address) == 105000000
  dai_oracle.updatePrice(MAX_DAI_PRICE + 1, transact={'from': owner})
  assert_fail(lambda: fixed_price_oracle.normalized_token_prices(DAI_token.address))

  dai_oracle.updatePrice(MIN_DAI_PRICE, transact={'from': owner})
  assert fixed_price_oracle.normalized_token_prices(DAI_token.address) == 95000000
  dai_oracle.updatePrice(MIN_DAI_PRICE - 1, transact={'from': owner})
  assert_fail(lambda: fixed_price_oracle.normalized_token_prices(DAI_token.address))


def test_pool_size(w3, fixed_contract, fixed_price_oracle, dai_oracle, DAI_token, USDC_token, assert_fail):
  owner = w3.eth.defaultAccount
  dai_oracle.updatePrice(DAI_PRICE, transact={'from': owner})

  fixed_price_oracle.updateTokenAddress(DAI_token.address, 0, transact={'from': owner})
  fixed_price_oracle.updateTokenAddress(USDC_token.address, 1, transact={'from': owner})

  DAI_token.transfer(owner, 10*10**18, transact={})
  DAI_token.approve(fixed_contract.address, 10*10**18, transact={'from': owner})
  fixed_contract.addLiquidity(DAI_token.address, 10*10**18, DEADLINE, transact={'from': owner})
  USDC_token.transfer(owner, 10*10**6, transact={})
  USDC_token.approve(fixed_contract.address, 10*10**6, transact={'from': owner})
  fixed_contract.addLiquidity(USDC_token.address, 10*10**6, DEADLINE, transact={'from': owner})
  assert fixed_contract.totalSupply() == 20.1 * 10**18
  assert fixed_price_oracle.poolSize(fixed_contract.address) == 20.1 * 10**18

  new_dai_price = DAI_PRICE + 10**16 # price will be 1.02 after that
  dai_oracle.updatePrice(new_dai_price, transact={'from': owner})
  assert fixed_contract.totalSupply() == 20.1 * 10**18
  assert fixed_price_oracle.poolSize(fixed_contract.address) == 20.2 * 10**18
