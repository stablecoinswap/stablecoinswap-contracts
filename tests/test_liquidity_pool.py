from tests.constants import (
    INITIAL_ETH,
    DEADLINE,
)

def test_initial_balances(w3, contract):
    a0, a1 = w3.eth.accounts[:2]
    # user
    assert contract.balanceOf(a1) == 0
    assert w3.eth.getBalance(a1) == INITIAL_ETH
    # contract
    assert w3.eth.getBalance(contract.address) == 0
    assert contract.totalSupply() == 0

def test_initial_liquidity(w3, contract, DAI_token, assert_fail):
    a0, a1 = w3.eth.accounts[:2]
    DAI_token.transfer(a1, 15*10**18, transact={})
    DAI_token.approve(contract.address, 15*10**18, transact={'from': a1})
    assert DAI_token.balanceOf(a1) == 15*10**18
    # initial liquidity value should be >= 10**9
    assert_fail(lambda: contract.addLiquidity(DAI_token.address, DEADLINE, transact={'value': 999999999, 'from': a1}))
    DAI_ADDED = 10**9
    contract.addLiquidity(DAI_token.address, DEADLINE, transact={'value': DAI_ADDED, 'from': a1})
    assert contract.totalSupply() == DAI_ADDED
    assert contract.balanceOf(a1) == DAI_ADDED
    assert contract.ownership(a1) == 1.0

def test_liquidity_pool(w3, contract, DAI_token, USDC_token, assert_fail):
    a0, a1, a2 = w3.eth.accounts[:3]
    DAI_token.transfer(a1, 15*10**18, transact={})
    DAI_token.approve(contract.address, 15*10**18, transact={'from': a1})
    DAI_ADDED = 10**9
    contract.addLiquidity(DAI_token.address, DEADLINE, transact={'value': DAI_ADDED, 'from': a1})

    USDC_token.transfer(a2, 15*10**18, transact={})
    USDC_token.approve(contract.address, 15*10**18, transact={'from': a2})
    USDC_ADDED = 3*10**9
    contract.addLiquidity(USDC_token.address, DEADLINE, transact={'value': USDC_ADDED, 'from': a2})

    assert contract.totalSupply() == DAI_ADDED + USDC_ADDED
    assert contract.balanceOf(a1) == DAI_ADDED
    assert contract.balanceOf(a2) == USDC_ADDED
    assert contract.ownership(a1) == 0.25
    assert contract.ownership(a2) == 0.75

    # deadline < block.timestamp
    assert_fail(lambda: contract.addLiquidity(DAI_token.address, 1, transact={'value': DAI_ADDED, 'from': a1}))
    # Can't transfer more liquidity than owned
    assert_fail(lambda: contract.transfer(a2, DAI_ADDED + 1, transact={'from': a1}))

    # Second liquidity provider (a2) transfers liquidity to first liquidity provider (a1)
    TRANSFERRED_AMOUNT = 10**9
    contract.transfer(a1, TRANSFERRED_AMOUNT, transact={'from': a2})
    assert contract.balanceOf(a1) == DAI_ADDED + TRANSFERRED_AMOUNT
    assert contract.balanceOf(a2) == USDC_ADDED - TRANSFERRED_AMOUNT
    assert contract.ownership(a1) == 0.5
    assert contract.ownership(a2) == 0.5
    assert w3.eth.getBalance(contract.address) == DAI_ADDED + USDC_ADDED
    assert DAI_token.balanceOf(contract.address) == DAI_ADDED
    assert USDC_token.balanceOf(contract.address) == USDC_ADDED

    # amount > owned (liquidity)
    assert_fail(lambda: contract.removeLiquidity(USDC_token.address, USDC_ADDED - TRANSFERRED_AMOUNT + 1, DEADLINE, transact={'from': a2}))
    # deadline < block.timestamp
    assert_fail(lambda: contract.removeLiquidity(USDC_token.address, TRANSFERRED_AMOUNT, 1, transact={'from': a2}))
    # amount > token liquidity
    assert_fail(lambda: contract.removeLiquidity(DAI_token.address, DAI_ADDED + 1, DEADLINE, transact={'from': a2}))

    # First and second liquidity providers remove their remaining liquidity
    contract.removeLiquidity(DAI_token.address, DAI_ADDED, DEADLINE, transact={'from': a2})
    contract.removeLiquidity(USDC_token.address, USDC_ADDED - TRANSFERRED_AMOUNT - DAI_ADDED, DEADLINE, transact={'from': a2})
    assert contract.ownership(a2) == 0
    assert contract.ownership(a1) == 1
    contract.removeLiquidity(USDC_token.address, DAI_ADDED + TRANSFERRED_AMOUNT, DEADLINE, transact={'from': a1})
    assert contract.totalSupply() == 0
    assert contract.balanceOf(a1) == 0
    assert contract.balanceOf(a2) == 0
    assert USDC_token.balanceOf(a1) == DAI_ADDED + TRANSFERRED_AMOUNT
    assert DAI_token.balanceOf(a2) == DAI_ADDED
    assert w3.eth.getBalance(contract.address) == 0
    assert DAI_token.balanceOf(contract.address) == 0
    assert USDC_token.balanceOf(contract.address) == 0

    # Can add liquidity again after all liquidity is divested
    contract.addLiquidity(DAI_token.address, DEADLINE, transact={'value': DAI_ADDED, 'from': a1})
