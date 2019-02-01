contract ERC20():
    def transfer(_to : address, _value : uint256) -> bool: modifying
    def transferFrom(_from : address, _to : address, _value : uint256) -> bool: modifying
    def balanceOf(_owner : address) -> uint256: constant

OwnershipTransferred: event({previous_owner: indexed(address), new_owner: indexed(address)})
LiquidityAdded: event({provider: indexed(address), amount: indexed(uint256)})
LiquidityRemoved: event({provider: indexed(address), amount: indexed(uint256)})
Trade: event({input_token: indexed(address), output_token: indexed(address), input_amount: indexed(uint256)})

name: public(bytes32)                             # Stablecoinswap
owner: public(address)                            # contract owner
decimals: public(uint256)                         # 18
totalSupply: public(uint256)                      # total number of contract tokens in existence
balances: uint256[address]                        # balance of an address
allowances: (uint256[address])[address]           # allowance of one address on another
supportedTokens: public(bool[address])                    # addresses of the ERC20 tokens traded on this contract

@public
def __init__(token_addresses: address[3]):
    self.owner = msg.sender
    self.name = 0x537461626c65636f696e73776170000000000000000000000000000000000000
    self.decimals = 18

    for i in range(3):
        assert token_addresses[i] != ZERO_ADDRESS
        self.supportedTokens[token_addresses[i]] = True

# Deposit stablecoins.
@public
def addLiquidity(token_address: address, amount: uint256, deadline: timestamp) -> bool:
    assert self.supportedTokens[token_address]
    assert deadline > block.timestamp and amount > 0

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
    assert self.supportedTokens[token_address]
    assert amount > 0 and deadline > block.timestamp

    self.balances[msg.sender] -= amount
    self.totalSupply -= amount
    assert ERC20(token_address).transfer(msg.sender, amount)
    log.LiquidityRemoved(msg.sender, amount)
    return True

# Trade one stablecoin for another
@public
def swapTokens(input_token: address, output_token: address, input_amount: uint256, limit_price: uint256, deadline: timestamp) -> bool:
    assert self.supportedTokens[input_token] and self.supportedTokens[output_token]
    assert input_amount > 0 and limit_price > 0
    assert deadline > block.timestamp

    # this should be pulled from an oracle later on
    current_price: uint256 = 1000000
    assert current_price <= limit_price
    output_amount: uint256 = input_amount * current_price / 1000000 / 1000 * 988

    assert ERC20(input_token).transferFrom(msg.sender, self, input_amount)
    assert ERC20(output_token).transfer(msg.sender, output_amount)

    log.Trade(input_token, output_token, input_amount)
    return True

@public
def addTokenSupport(token_address: address) -> bool:
    assert not self.supportedTokens[token_address]
    self.supportedTokens[token_address] = True
    return True

@public
def removeTokenSupport(token_address: address) -> bool:
    assert self.supportedTokens[token_address]
    del self.supportedTokens[token_address]
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

# ERC20 compatibility for exchange liquidity modified from
# https://github.com/ethereum/vyper/blob/master/examples/tokens/ERC20.vy

@public
@constant
def balanceOf(_owner : address) -> uint256:
    return self.balances[_owner]

@public
def transfer(_to : address, _value : uint256) -> bool:
    self.balances[msg.sender] -= _value
    self.balances[_to] += _value
    return True

@public
def transferFrom(_from : address, _to : address, _value : uint256) -> bool:
    self.balances[_from] -= _value
    self.balances[_to] += _value
    self.allowances[_from][msg.sender] -= _value
    return True

@public
def approve(_spender : address, _value : uint256) -> bool:
    self.allowances[msg.sender][_spender] = _value
    return True

@public
@constant
def allowance(_owner : address, _spender : address) -> uint256:
    return self.allowances[_owner][_spender]
