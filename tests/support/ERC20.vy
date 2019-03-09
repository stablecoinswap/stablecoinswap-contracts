# THIS CONTRACT IS FOR TESTING PURPOSES AND IS NOT PART OF THE PROJECT

Transfer: event({_from: indexed(address), _to: indexed(address), _value: uint256})
Approval: event({_owner: indexed(address), _spender: indexed(address), _value: uint256})

name: public(string[64])
symbol: public(string[32])
decimals: public(uint256)
balances: map(address, uint256)
allowances: map(address, map(address, uint256))
totalSupply: public(uint256)
owner: address

@public
def __init__(_name: string[64], _symbol: string[32], _decimals: uint256, _supply: uint256):
    self.name = _name
    self.symbol = _symbol
    self.decimals = _decimals
    self.balances[msg.sender] = _supply
    self.totalSupply = _supply
    self.owner = msg.sender
    log.Transfer(ZERO_ADDRESS, msg.sender, _supply)

@public
@constant
def balanceOf(_owner : address) -> uint256:
    return self.balances[_owner]

@public
def transfer(_to : address, _value : uint256) -> bool:
    self.balances[msg.sender] -= _value
    self.balances[_to] += _value
    log.Transfer(msg.sender, _to, _value)
    return True

@public
def transferFrom(_from : address, _to : address, _value : uint256) -> bool:
    self.balances[_from] -= _value
    self.balances[_to] += _value
    self.allowances[_from][msg.sender] -= _value
    log.Transfer(_from, _to, _value)
    return True

@public
def approve(_spender : address, _value : uint256) -> bool:
    self.allowances[msg.sender][_spender] = _value
    log.Approval(msg.sender, msg.sender, _value)
    return True

@public
@constant
def allowance(_owner : address, _spender : address) -> uint256:
    return self.allowances[_owner][_spender]

@public
def mint(_to: address, _value: uint256) -> bool:
    assert msg.sender == self.owner
    assert _to != ZERO_ADDRESS
    self.totalSupply += _value
    self.balances[_to] += _value
    log.Transfer(ZERO_ADDRESS, _to, _value)
    return True
