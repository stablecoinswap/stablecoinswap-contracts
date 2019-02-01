# @title Stablecoinwap Interface

name: public(bytes32)                             # Stablecoinswap
owner: public(address)                            # owner
decimals: public(uint256)                         # 18
totalSupply: public(uint256)                      # total number of contract tokens in existence
balances: uint256[address]                        # balance of an address
allowances: (uint256[address])[address]           # allowance of one address on another
availableTokens: address[3]                       # addresses of the ERC20 tokens traded on this contract
currentToken: address(ERC20)

# @notice contract constructor
@public
def __init__(_owner: address, token_addresses: address[3]):
    assert self.owner == ZERO_ADDRESS
    assert _owner != ZERO_ADDRESS

    self.name = 0x537461626c65636f696e73776170000000000000000000000000000000000000
    self.owner = _owner
    self.decimals = 18

    for i in range(3):
        assert token_addresses[i] != ZERO_ADDRESS
        self.availableTokens[i] = token_addresses[i]

# @notice Deposit stablecoins.
# @param token_symbol Symbol of stablecoin to deposit.
# @param deadline Time after which this transaction can no longer be executed.
# @return The amount of stablecoins added.
@public
@payable
def addLiquidity(token_addr: address, deadline: timestamp) -> uint256:
    assert token_addr in self.availableTokens
    self.currentToken = token_addr
    assert deadline > block.timestamp and msg.value > 0
    total_liquidity: uint256 = self.totalSupply
    if total_liquidity > 0:
        liquidity_added: uint256 = as_unitless_number(msg.value)
        self.balances[msg.sender] += liquidity_added
        self.totalSupply = total_liquidity + liquidity_added
        assert self.currentToken.transferFrom(msg.sender, self, liquidity_added)
        return liquidity_added
    else:
        assert msg.value >= 1000000000
        initial_liquidity: uint256 = as_unitless_number(self.balance)
        self.totalSupply = initial_liquidity
        self.balances[msg.sender] = initial_liquidity
        assert self.currentToken.transferFrom(msg.sender, self, initial_liquidity)
        return initial_liquidity

# @dev Withdraw ETH and stablecoins.
# @param token_symbol Symbol of stablecoin to withdraw.
# @param amount Amount of stablecoins withdrawn.
# @param deadline Time after which this transaction can no longer be executed.
# @return The amount of ETH and stablecoins withdrawn.
@public
def removeLiquidity(token_addr: address, amount: uint256, deadline: timestamp) -> (uint256(wei), uint256):
    assert token_addr in self.availableTokens
    self.currentToken = token_addr
    assert amount > 0 and deadline > block.timestamp
    total_liquidity: uint256 = self.totalSupply
    assert total_liquidity > 0
    assert self.currentToken.balanceOf(self) >= amount
    eth_amount: uint256(wei) = amount * self.balance / total_liquidity
    self.balances[msg.sender] -= amount
    self.totalSupply = total_liquidity - amount
    send(msg.sender, eth_amount)
    assert self.currentToken.transfer(msg.sender, amount)
    return eth_amount, amount

# @dev Check if token is supported or not.
# @param symbol Symbol of token
@public
@constant
def tokenIsSupported(token_addr: address) -> bool:
    return token_addr in self.availableTokens

# @dev Return share of total liquidity that owns to user
# @param user_address Address of owner
@public
@constant
def ownership(user_address: address) -> decimal:
    user_balance: decimal = convert(self.balances[user_address], decimal)
    total_liquidity: decimal = convert(self.totalSupply, decimal)
    share: decimal = user_balance / total_liquidity
    return share

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
