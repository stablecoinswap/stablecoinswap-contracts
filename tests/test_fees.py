from decimal import Decimal

def test_fees(w3, contract, assert_fail):
  owner = w3.eth.defaultAccount
  user = w3.eth.accounts[1]

  # initial values
  assert contract.fees('tradeFee') == Decimal('0.002')
  assert contract.fees('ownerFee') == Decimal('0.001')

  # only owner can change fees
  assert_fail(lambda: contract.updateFee('tradeFee', Decimal('0.003'), transact={'from': user}))
  # fee can't be negative
  assert_fail(lambda: contract.updateFee('tradeFee', Decimal('-0.003'), transact={'from': owner}))
  contract.updateFee('tradeFee', Decimal('0.003'))
  assert contract.fees('tradeFee') == Decimal('0.002')
  contract.updateFee('tradeFee', Decimal('0.003'), transact={'from': owner})
  assert contract.fees('tradeFee') == Decimal('0.003')
  contract.updateFee('ownerFee', Decimal('0.004'), transact={'from': owner})
  assert contract.fees('ownerFee') == Decimal('0.004')
