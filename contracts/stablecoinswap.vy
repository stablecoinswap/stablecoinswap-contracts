contract ERC20():
    def transfer(_to : address, _value : uint256) -> bool: modifying
    def transferFrom(_from : address, _to : address, _value : uint256) -> bool: modifying
    def balanceOf(_owner : address) -> uint256: constant

OwnershipTransferred: event({previous_owner: indexed(address), new_owner: indexed(address)})

name: public(bytes32)                             # Stablecoinswap
owner: public(address)                            # contract owner
decimals: public(uint256)                         # 18
totalSupply: public(uint256)                      # total number of contract tokens in existence
balances: uint256[address]                        # balance of an address
allowances: (uint256[address])[address]           # allowance of one address on another
availableTokens: address[3]                       # addresses of the ERC20 tokens traded on this contract

@public
def __init__(token_addresses: address[3]):
    self.owner = msg.sender
    self.name = 0x537461626c65636f696e73776170000000000000000000000000000000000000
    self.decimals = 18

    for i in range(3):
        assert token_addresses[i] != ZERO_ADDRESS
        self.availableTokens[i] = token_addresses[i]

# Deposit stablecoins.
@public
def addLiquidity(token_address: address, amount: uint256, deadline: timestamp) -> bool:
    assert token_address in self.availableTokens
    assert deadline > block.timestamp and amount > 0

    if self.totalSupply > 0:
        self.balances[msg.sender] += amount
        self.totalSupply += amount
    else:
        assert amount >= 1000000000
        self.balances[msg.sender] = amount
        self.totalSupply = amount

    assert ERC20(token_address).transferFrom(msg.sender, self, amount)
    return True

# Withdraw stablecoins.
@public
def removeLiquidity(token_address: address, amount: uint256, deadline: timestamp) -> uint256:
    assert token_address in self.availableTokens
    assert amount > 0 and deadline > block.timestamp
    assert self.totalSupply > 0
    assert ERC20(token_address).balanceOf(self) >= amount

    self.balances[msg.sender] -= amount
    self.totalSupply = self.totalSupply - amount
    assert ERC20(token_address).transfer(msg.sender, amount)
    return amount

@public
@constant
def tokenIsSupported(token_address: address) -> bool:
    return token_address in self.availableTokens

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
