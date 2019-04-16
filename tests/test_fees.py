from decimal import Decimal

def test_fees(w3, contract, assert_fail):
  owner = w3.eth.defaultAccount
  user = w3.eth.accounts[1]

  # initial values
  assert contract.fees(b'tradeFee') == Decimal('0.002')
  assert contract.fees(b'ownerFee') == Decimal('0.001')

  # only owner can change fees
  assert_fail(lambda: contract.updateFee(b'tradeFee', Decimal('0.003'), transact={'from': user}))
  contract.updateFee(b'tradeFee', Decimal('0.003'))
  assert contract.fees(b'tradeFee') == Decimal('0.002')
  contract.updateFee(b'tradeFee', Decimal('0.003'), transact={'from': owner})
  assert contract.fees(b'tradeFee') == Decimal('0.003')
  contract.updateFee(b'ownerFee', Decimal('0.004'), transact={'from': owner})
  assert contract.fees(b'ownerFee') == Decimal('0.004')
