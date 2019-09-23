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
def create_contract(w3, path, *args):
    wd = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(wd, os.pardir, path)) as f:
        source = f.read()
    out = compiler.compile_code(source, ['abi', 'bytecode'])
    abi = out['abi']
    bytecode = out['bytecode']

    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    deploy_transaction = {
        'from': w3.eth.defaultAccount,
        'data': contract._encode_constructor_data(args, {}),
        'value': 0,
        'gasPrice': 0
    }
    tx_hash = w3.eth.sendTransaction(deploy_transaction)
    address = w3.eth.getTransactionReceipt(tx_hash)['contractAddress']
    contract = ConciseContract(w3.eth.contract(
        address,
        abi=abi,
        bytecode=bytecode
    ))
    return contract

@pytest.fixture
def DAI_token(w3):
    args = ['DAI Test Token', 'DAI', 18, 100000*10**18]
    contract = create_contract(w3, 'tests/support/ERC20.vy', *args)
    return contract

@pytest.fixture
def GUSD_token(w3):
    args = ['Gemini Test Token', 'GUSD', 2, 100000*10**2]
    contract = create_contract(w3, 'tests/support/ERC20.vy', *args)
    return contract

@pytest.fixture
def USDC_token(w3):
    args = ['USDC Test Token', 'USDC', 6, 100000*10**6]
    contract = create_contract(w3, 'tests/support/ERC20.vy', *args)
    return contract

@pytest.fixture
def ZUSD_token(w3):
    args = ['Zero Test Token', 'ZUSD', 1, 100000*10]
    contract = create_contract(w3, 'tests/support/ERC20.vy', *args)
    return contract

@pytest.fixture
def price_oracle(w3):
    contract = create_contract(w3, 'contracts/priceoracle.vy', *[])
    return contract

@pytest.fixture
def dai_oracle(w3):
    contract = create_contract(w3, 'tests/support/dai_price_oracle.vy', *[])
    return contract

@pytest.fixture
def fixed_price_oracle(w3, DAI_token, dai_oracle):
    args = [DAI_token.address, dai_oracle.address]
    contract = create_contract(w3, 'contracts/fixed_price_oracle.vy', *args)
    return contract

@pytest.fixture
def contract(w3, DAI_token, GUSD_token, USDC_token, price_oracle):
    available_tokens = [DAI_token.address, USDC_token.address, GUSD_token.address]
    args = [available_tokens, price_oracle.address]
    contract = create_contract(w3, 'contracts/stablecoinswap.vy', *args)
    return contract

@pytest.fixture
def fixed_contract(w3, DAI_token, GUSD_token, USDC_token, fixed_price_oracle):
    available_tokens = [DAI_token.address, USDC_token.address, GUSD_token.address]
    args = [available_tokens, fixed_price_oracle.address]
    contract = create_contract(w3, 'contracts/stablecoinswap.vy', *args)
    return contract

@pytest.fixture
def proxy_contract(w3, fixed_contract):
    args = [fixed_contract.address]
    contract = create_contract(w3, 'contracts/proxy.vy', *args)
    return contract

@pytest.fixture
def assert_fail():
    def assert_fail(func):
        with raises(Exception):
            func()
    return assert_fail
