import os
import pytest
from pytest import raises

from web3 import Web3
from web3.contract import ConciseContract
import eth_tester
from eth_tester import EthereumTester, PyEVMBackend
from eth_tester.exceptions import TransactionFailed
from vyper import compiler

from tests.constants import (
    ZERO_ADDR
)

setattr(eth_tester.backends.pyevm.main, 'GENESIS_GAS_LIMIT', 10**9)
setattr(eth_tester.backends.pyevm.main, 'GENESIS_DIFFICULTY', 1)

@pytest.fixture
def tester():
    return EthereumTester(backend=PyEVMBackend())

@pytest.fixture
def w3(tester):
    w3 = Web3(Web3.EthereumTesterProvider(tester))
    w3.eth.setGasPriceStrategy(lambda web3, params: 0)
    w3.eth.defaultAccount = w3.eth.accounts[0]
    return w3

@pytest.fixture
def pad_bytes32():
    def pad_bytes32(instr):
        """ Pad a string \x00 bytes to return correct bytes32 representation. """
        bstr = instr.encode()
        return bstr + (32 - len(bstr)) * b'\x00'
    return pad_bytes32

# @pytest.fixture
def create_contract(w3, path):
    wd = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(wd, os.pardir, path)) as f:
        source = f.read()
    bytecode = '0x' + compiler.compile(source).hex()
    abi = compiler.mk_full_signature(source)
    return w3.eth.contract(abi=abi, bytecode=bytecode)

@pytest.fixture
def exchange_template(w3):
    deploy = create_contract(w3, 'contracts/example.vy')
    tx_hash = deploy.constructor().transact()
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    return ConciseContract(w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=deploy.abi
    ))

@pytest.fixture
def DAI_token(w3):
    deploy = create_contract(w3, 'contracts/test_contracts/ERC20.vy')
    tx_hash = deploy.constructor(b'DAI Test Token', b'DAI', 18, 100000*10**18).transact()
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    return ConciseContract(w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=deploy.abi
    ))

@pytest.fixture
def USDC_token(w3):
    deploy = create_contract(w3, 'contracts/test_contracts/ERC20.vy')
    tx_hash = deploy.constructor(b'USDC Test Token', b'USDC', 18, 100000*10**18).transact()
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    return ConciseContract(w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=deploy.abi
    ))

@pytest.fixture
def TUSD_token(w3):
    deploy = create_contract(w3, 'contracts/test_contracts/ERC20.vy')
    tx_hash = deploy.constructor(b'TUSD Test Token', b'TUSD', 18, 100000*10**18).transact()
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    return ConciseContract(w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=deploy.abi
    ))

@pytest.fixture
def contract(w3, DAI_token, USDC_token, TUSD_token):
    deploy = create_contract(w3, 'contracts/stablecoinswap.vy')
    available_tokens = [DAI_token.address, USDC_token.address, TUSD_token.address]
    tx_hash = deploy.constructor(w3.eth.accounts[0], available_tokens).transact()
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    contract = ConciseContract(w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=deploy.abi
    ))
    return contract

@pytest.fixture
def assert_fail():
    def assert_fail(func):
        with raises(Exception):
            func()
    return assert_fail
