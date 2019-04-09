from decimal import (
    Decimal,
)

def test_price_oracle(w3, DAI_token, price_oracle, assert_fail):
  owner = w3.eth.accounts[0]
  user = w3.eth.accounts[1]

  assert price_oracle.name() == 'PriceOracle'
  assert price_oracle.tokens(DAI_token.address) == 0

  # only owner can update token price
  assert_fail(lambda: price_oracle.updatePrice(DAI_token.address, 97734655, transact={'from': user}))
  price_oracle.updatePrice(DAI_token.address, 97734655, transact={'from': owner})
  assert price_oracle.tokens(DAI_token.address) == 97734655
  price_oracle.updatePrice(DAI_token.address, 103349913, transact={'from': owner})
  assert price_oracle.tokens(DAI_token.address) == 103349913

def test_price_oracle_address(w3, contract, price_oracle, assert_fail):
    owner = w3.eth.defaultAccount
    user = w3.eth.accounts[1]
    new_address = w3.eth.accounts[2]

    assert contract.priceOracleAddress() == price_oracle.address
    assert_fail(lambda: contract.updatePriceOracleAddress(new_address, transact={'from': user}))
    contract.updatePriceOracleAddress(new_address, transact={'from': owner})
    assert contract.priceOracleAddress() == new_address
