from pytest import raises
from web3.contract import ConciseContract
from eth_tester.exceptions import TransactionFailed
from tests.constants import (
    ZERO_ADDR
)

def test_contract(w3, contract, pad_bytes32):
  assert contract.owner() == w3.eth.defaultAccount
  assert contract.name() == pad_bytes32('Stablecoinswap')
  assert contract.decimals() == 18
  assert contract.totalSupply() == 0
  # check used tokens
  assert contract.tokenIsSupported('DAI'.encode())
  assert contract.tokenIsSupported('USDC'.encode())
  assert contract.tokenIsSupported('TUSD'.encode())
  assert not contract.tokenIsSupported('WETH'.encode())
