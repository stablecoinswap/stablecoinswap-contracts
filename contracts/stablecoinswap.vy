contract ERC20():
    def transfer(_to : address, _value : uint256) -> bool: modifying
    def transferFrom(_from : address, _to : address, _value : uint256) -> bool: modifying
    def balanceOf(_owner : address) -> uint256: constant

# ERC20 events
Transfer: event({_from: indexed(address), _to: indexed(address), _value: uint256})
Approval: event({_owner: indexed(address), _spender: indexed(address), _value: uint256})

OwnershipTransferred: event({previous_owner: indexed(address), new_owner: indexed(address)})
LiquidityAdded: event({provider: indexed(address), amount: indexed(uint256)})
LiquidityRemoved: event({provider: indexed(address), amount: indexed(uint256)})
Trade: event({input_token: indexed(address), output_token: indexed(address), input_amount: indexed(uint256)})
PermissionUpdated: event({name: indexed(bytes[32]), value: indexed(bool)})

name: public(bytes[32])                           # Stablecoinswap
owner: public(address)                            # contract owner
decimals: public(uint256)                         # 18
totalSupply: public(uint256)                      # total number of contract tokens in existence
balances: map(address, uint256)                   # balance of an address
allowances: map(address, map(address, uint256))   # allowance of one address on another
inputTokens: public(map(address, bool))           # addresses of the ERC20 tokens allowed to transfer into this contract
outputTokens: public(map(address, bool))          # addresses of the ERC20 tokens allowed to transfer out of this contract
permissions: public(map(bytes[32], bool))         # pause / resume contract functions

@public
def __init__(token_addresses: address[3]):
    self.owner = msg.sender
    self.name = "Stablecoinswap"
    self.decimals = 18
    self.permissions["tradingAllowed"] = True
    self.permissions["liquidityAddingAllowed"] = True
    self.permissions["liquidityRemovingAllowed"] = True

    for i in range(3):
        assert token_addresses[i] != ZERO_ADDRESS
        self.inputTokens[token_addresses[i]] = True
        self.outputTokens[token_addresses[i]] = True

# Deposit stablecoins.
@public
def addLiquidity(token_address: address, amount: uint256, deadline: timestamp) -> bool:
    assert self.inputTokens[token_address]
    assert deadline > block.timestamp and amount > 0
    assert self.permissions["liquidityAddingAllowed"]

    if self.totalSupply > 0:
        self.balances[msg.sender] += amount
        self.totalSupply += amount
    else:
        assert amount >= 1000000000
        self.balances[msg.sender] = amount
        self.totalSupply = amount

    assert ERC20(token_address).transferFrom(msg.sender, self, amount)
    log.LiquidityAdded(msg.sender, amount)
    return True

# Withdraw stablecoins.
@public
def removeLiquidity(token_address: address, amount: uint256, deadline: timestamp) -> bool:
    assert self.outputTokens[token_address]
    assert amount > 0 and deadline > block.timestamp
    assert self.permissions["liquidityRemovingAllowed"]

    self.balances[msg.sender] -= amount
    self.totalSupply -= amount
    assert ERC20(token_address).transfer(msg.sender, amount)
    log.LiquidityRemoved(msg.sender, amount)
    return True

# Trade one stablecoin for another
@public
def swapTokens(input_token: address, output_token: address, input_amount: uint256, limit_price: uint256, deadline: timestamp) -> bool:
    assert self.inputTokens[input_token] and self.outputTokens[output_token]
    assert input_amount > 0 and limit_price > 0
    assert deadline > block.timestamp
    assert self.permissions["tradingAllowed"]

    # this should be pulled from an oracle later on
    current_price: uint256 = 1000000
    assert current_price <= limit_price
    output_amount: uint256 = input_amount * current_price / 1000000 / 1000 * 998

    assert ERC20(input_token).transferFrom(msg.sender, self, input_amount)
    assert ERC20(output_token).transfer(msg.sender, output_amount)

    log.Trade(input_token, output_token, input_amount)
    return True

@public
def updateInputToken(token_address: address, allowed: bool) -> bool:
    assert msg.sender == self.owner
    assert not self.inputTokens[token_address] == allowed
    self.inputTokens[token_address] = allowed
    return True

@public
def updateOutputToken(token_address: address, allowed: bool) -> bool:
    assert msg.sender == self.owner
    assert not self.outputTokens[token_address] == allowed
    self.outputTokens[token_address] = allowed
    return True

@public
def updatePermission(permission_name: bytes[32], value: bool) -> bool:
    assert msg.sender == self.owner
    self.permissions[permission_name] = value
    log.PermissionUpdated(permission_name, value)
    return True

# Return share of total liquidity that owns to user
@public
@constant
def poolOwnership(user_address: address) -> decimal:
    user_balance: decimal = convert(self.balances[user_address], decimal)
    total_liquidity: decimal = convert(self.totalSupply, decimal)
    share: decimal = user_balance / total_liquidity
    return share

@public
def transferOwnership(new_owner: address) -> bool:
    assert new_owner != ZERO_ADDRESS
    assert msg.sender == self.owner
    self.owner = new_owner
    log.OwnershipTransferred(self.owner, new_owner)
    return True

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
