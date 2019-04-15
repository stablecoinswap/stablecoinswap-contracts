from decimal import (
    Decimal,
)

from tests.constants import (
    DEADLINE
)

def test_price_oracle(w3, DAI_token, price_oracle, assert_fail):
  owner = w3.eth.accounts[0]
  user = w3.eth.accounts[1]

  assert price_oracle.name() == 'PriceOracle'
  assert price_oracle.token_prices(DAI_token.address) == 0

  # only owner can update token price
  assert_fail(lambda: price_oracle.updatePrice(DAI_token.address, 97734655, transact={'from': user}))
  # price validations
  assert_fail(lambda: price_oracle.updatePrice(DAI_token.address, 9999999, transact={'from': user}))
  assert_fail(lambda: price_oracle.updatePrice(DAI_token.address, 10000000001, transact={'from': user}))

  price_oracle.updatePrice(DAI_token.address, 97734655, transact={'from': owner})
  assert price_oracle.token_prices(DAI_token.address) == 97734655
  price_oracle.updatePrice(DAI_token.address, 103349913, transact={'from': owner})
  assert price_oracle.token_prices(DAI_token.address) == 103349913

def test_pool_size(w3, contract, price_oracle, DAI_token, USDC_token, assert_fail):
  owner = w3.eth.defaultAccount
  user = w3.eth.accounts[1]

  price_oracle.updatePrice(DAI_token.address, 2 * 10**8, transact={'from': owner})
  price_oracle.updatePrice(USDC_token.address, 3 * 10**8, transact={'from': owner})
  price_oracle.updateTokenAddress(DAI_token.address, 0, transact={'from': owner})
  price_oracle.updateTokenAddress(USDC_token.address, 1, transact={'from': owner})

  DAI_token.transfer(owner, 10*10**18, transact={})
  DAI_token.approve(contract.address, 10*10**18, transact={'from': owner})
  contract.addLiquidity(DAI_token.address, 10*10**18, DEADLINE, transact={'from': owner})
  USDC_token.transfer(owner, 10*10**6, transact={})
  USDC_token.approve(contract.address, 10*10**6, transact={'from': owner})
  contract.addLiquidity(USDC_token.address, 10*10**6, DEADLINE, transact={'from': owner})
  assert contract.totalSupply() == 50 * 10**18
  assert price_oracle.poolSize(contract.address) == 50 * 10**18

  price_oracle.updatePrice(DAI_token.address, 3 * 10**8, transact={'from': owner})
  assert contract.totalSupply() == 50 * 10**18
  assert price_oracle.poolSize(contract.address) == 60 * 10**18

def test_price_oracle_address(w3, contract, price_oracle, assert_fail):
  owner = w3.eth.defaultAccount
  user = w3.eth.accounts[1]
  new_address = w3.eth.accounts[2]

  assert contract.priceOracleAddress() == price_oracle.address
  assert_fail(lambda: contract.updatePriceOracleAddress(new_address, transact={'from': user}))
  contract.updatePriceOracleAddress(new_address, transact={'from': owner})
  assert contract.priceOracleAddress() == new_address
