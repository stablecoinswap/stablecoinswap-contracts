from pytest import raises
from web3.contract import ConciseContract
from eth_tester.exceptions import TransactionFailed
from tests.constants import (
    ZERO_ADDR
)

def test_contract(w3, contract, DAI_token, USDC_token):
  assert contract.owner() == w3.eth.defaultAccount
  assert contract.name() == b'Stablecoinswap'
  assert contract.decimals() == 18
  assert contract.totalSupply() == 0
  # check used tokens
  assert DAI_token.address in contract.availableInputTokens()
  assert not w3.eth.accounts[1] in contract.availableInputTokens()
  assert USDC_token.address in contract.availableOutputTokens()
  assert not w3.eth.accounts[1] in contract.availableOutputTokens()
