from pytest import raises
from web3.contract import ConciseContract
from eth_tester.exceptions import TransactionFailed
from tests.constants import (
    ZERO_ADDR
)

def test_ownership(w3, contract, assert_fail):
  old_owner = w3.eth.defaultAccount
  new_owner = w3.eth.accounts[1]
  assert contract.owner() == old_owner
  # new owner address can't be empty
  assert_fail(lambda: contract.transferOwnership(ZERO_ADDR, transact={'from': old_owner}))
  assert contract.transferOwnership(new_owner, transact={'from': old_owner})
  assert contract.owner() == new_owner
  # this function should be called by owner
  assert_fail(lambda: contract.transferOwnership(old_owner, transact={'from': old_owner}))
