# THIS CONTRACT IS FOR TESTING PURPOSES AND IS NOT PART OF THE PROJECT

GAS_PRICE: constant(uint256) = 20000000000

reqc: map(address, uint256)
cbAddresses: public(map(address, bytes[1]))
offchainPayment: public(map(address, bool))

owner: address
paymentFlagger: address
addr_gasPrice: map(address, uint256)
addr_proofType: map(address, bytes[1])
price: map(bytes32, uint256)

@public
def __init__():
    self.owner = msg.sender

@public
def changeAdmin(_newAdmin: address):
    assert self.owner == msg.sender
    self.owner = _newAdmin

@public
def changePaymentFlagger(_newFlagger: address):
    assert self.owner == msg.sender
    self.paymentFlagger = _newFlagger

@public
def addCbAddress(newCbAddress: address, addressType: bytes[1]):
    assert self.owner == msg.sender
    self.cbAddresses[newCbAddress] = addressType

@public
def removeCbAddress(newCbAddress: address):
    assert self.owner == msg.sender
    clear(self.cbAddresses[newCbAddress])

@public
@constant
def cbAddress() -> address:
    if self.cbAddresses[tx.origin] != b'\x00':
        return tx.origin
    else:
        return ZERO_ADDRESS

@public
def getPrice(_datasource: bytes[20]) -> uint256:
    _gasprice: uint256 = self.addr_gasPrice[msg.sender]
    _gaslimit: uint256 = 200000

    if ((self.reqc[msg.sender] == 0) and (_gasprice <= GAS_PRICE) and (tx.origin != self.cbAddress())):
        return 0

    if _gasprice == 0:
        _gasprice = GAS_PRICE

    _dsprice: uint256 = self.price[sha3(concat(convert(_datasource, bytes32), convert(self.addr_proofType[msg.sender], bytes32)))]
    _dsprice += _gaslimit * _gasprice
    return _dsprice

@public
def query(_timestamp: timestamp, _datasource: bytes[20], _arg: string[100]) -> bytes32:
    assert _timestamp <= block.timestamp + 3600 * 24 * 60
    _id: bytes32 = sha3(concat(convert(self, bytes32), convert(msg.sender, bytes32), convert(self.reqc[msg.sender], bytes32)))
    self.reqc[msg.sender] += 1
    return _id

@public
def query2(_timestamp: timestamp, _datasource: bytes[20], _arg1: string[100], _arg2: string[160]) -> bytes32:
    assert _timestamp <= block.timestamp + 3600 * 24 * 60
    _id: bytes32 = sha3(concat(convert(self, bytes32), convert(msg.sender, bytes32), convert(self.reqc[msg.sender], bytes32)))
    self.reqc[msg.sender] += 1
    return _id

@public
@payable
def __default__():
    pass
