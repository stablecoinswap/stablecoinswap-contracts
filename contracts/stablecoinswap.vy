contract ERC20():
    def transfer(_to: address, _value: uint256) -> bool: modifying
    def transferFrom(_from: address, _to: address, _value: uint256) -> bool: modifying
    def balanceOf(_owner: address) -> uint256: constant
    def allowance(_owner: address, _spender: address) -> uint256: constant
    def decimals() -> uint256: constant

contract PriceOracle():
    def poolSize(contract_address: address) -> uint256: constant
    def token_prices(token_address: address) -> uint256: constant

TOKEN_PRICE_MULTIPLIER: constant(uint256) = 100000000

# ERC20 events
Transfer: event({_from: indexed(address), _to: indexed(address), _value: uint256})
Approval: event({_owner: indexed(address), _spender: indexed(address), _value: uint256})

OwnershipTransferred: event({previous_owner: indexed(address), new_owner: indexed(address)})
LiquidityAdded: event({provider: indexed(address), amount: indexed(uint256)})
LiquidityRemoved: event({provider: indexed(address), amount: indexed(uint256)})
Trade: event({input_token: indexed(address), output_token: indexed(address), input_amount: indexed(uint256)})
PermissionUpdated: event({name: indexed(bytes[32]), value: indexed(bool)})
FeeUpdated: event({name: indexed(bytes[32]), value: indexed(decimal)})
PriceOracleAddressUpdated: event({new_address: indexed(address)})
Payment: event({amount: uint256(wei), _from: indexed(address)})

name: public(bytes[32])                           # Stablecoinswap
owner: public(address)                            # contract owner
decimals: public(uint256)                         # 18
totalSupply: public(uint256)                      # total number of contract tokens in existence
balances: map(address, uint256)                   # balance of an address
allowances: map(address, map(address, uint256))   # allowance of one address on another
inputTokens: public(map(address, bool))           # addresses of the ERC20 tokens allowed to transfer into this contract
outputTokens: public(map(address, bool))          # addresses of the ERC20 tokens allowed to transfer out of this contract
permissions: public(map(bytes[32], bool))         # pause / resume contract functions
feesInt: map(bytes[32], int128)                   # trade / pool fees multiplied by 1000
priceOracleAddress: public(address)               # address of price oracle

@public
def __init__(token_addresses: address[3], price_oracle_addr: address):
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

    self.feesInt['tradeFee'] = 2
    self.feesInt['ownerFee'] = 1

    self.priceOracleAddress = price_oracle_addr

# Deposit stablecoins.
@public
def addLiquidity(token_address: address, amount: uint256, deadline: timestamp) -> bool:
    assert self.inputTokens[token_address]
    assert deadline > block.timestamp and amount > 0
    assert self.permissions["liquidityAddingAllowed"]
    assert ERC20(token_address).balanceOf(msg.sender) >= amount
    assert ERC20(token_address).allowance(msg.sender, self) >= amount

    new_liquidity: uint256 = PriceOracle(self.priceOracleAddress).token_prices(token_address) * amount / TOKEN_PRICE_MULTIPLIER * 10**(self.decimals - ERC20(token_address).decimals())
    if self.totalSupply > 0:
        new_liquidity = new_liquidity * self.totalSupply / PriceOracle(self.priceOracleAddress).poolSize(self)
    else:
        assert new_liquidity >= 1000000000

    ERC20(token_address).transferFrom(msg.sender, self, amount)
    self.balances[msg.sender] += new_liquidity
    self.totalSupply += new_liquidity
    log.LiquidityAdded(msg.sender, new_liquidity)

    return True

# Withdraw stablecoins.
@public
def removeLiquidity(token_address: address, amount: uint256, deadline: timestamp) -> bool:
    assert self.outputTokens[token_address]
    assert amount > 0 and deadline > block.timestamp
    assert self.balances[msg.sender] >= amount
    assert self.permissions["liquidityRemovingAllowed"]

    token_price: uint256 = PriceOracle(self.priceOracleAddress).token_prices(token_address)
    assert token_price > 0 and self.totalSupply > 0
    # usd_amount = amount(in contract tokens) * poolSize / totalSupply
    # token_amount = usd_amount / token_price
    token_amount: uint256 = amount * PriceOracle(self.priceOracleAddress).poolSize(self) / self.totalSupply

    tradeFee: uint256 = 0
    ownerFee: uint256 = 0

    if msg.sender != self.owner:
        ownerFee = amount * convert(self.feesInt['ownerFee'], uint256) / 1000
        token_amount = token_amount * convert(1000 - self.feesInt['ownerFee'] - self.feesInt['tradeFee'], uint256) / 1000

    # convert contract tokens to selected by user
    # some tokens have 18 decimals, some - 6 decimals (so we have token_multiplier and token_divider)
    # token_amount = contract_amount / token_price * token_multiplier / token_divider
    token_amount = token_amount * TOKEN_PRICE_MULTIPLIER / token_price / 10**(self.decimals - ERC20(token_address).decimals())

    ERC20(token_address).transfer(msg.sender, token_amount)
    self.balances[msg.sender] -= amount
    self.balances[self.owner] += ownerFee
    self.totalSupply -= amount - ownerFee
    log.LiquidityRemoved(msg.sender, amount)

    return True

# Trade one stablecoin for another
@public
def swapTokens(input_token: address, output_token: address, input_amount: uint256, min_output_amount: uint256, deadline: timestamp) -> bool:
    assert self.inputTokens[input_token] and self.outputTokens[output_token]
    assert input_amount > 0 and min_output_amount > 0
    assert deadline > block.timestamp
    assert self.permissions["tradingAllowed"]
    assert ERC20(input_token).balanceOf(msg.sender) >= input_amount
    assert ERC20(input_token).allowance(msg.sender, self) >= input_amount

    input_token_price: uint256 = PriceOracle(self.priceOracleAddress).token_prices(input_token)
    output_token_price: uint256 = PriceOracle(self.priceOracleAddress).token_prices(output_token)

    token_multiplier: uint256 = 10**(self.decimals - ERC20(input_token).decimals())
    output_amount: uint256 = input_amount * token_multiplier * input_token_price / output_token_price
    tradeFee: uint256 = output_amount * convert(self.feesInt['tradeFee'], uint256) / 1000
    ownerFee: uint256 = output_amount * convert(self.feesInt['ownerFee'], uint256) / 1000
    output_amount -= tradeFee + ownerFee

    pool_size: uint256 = PriceOracle(self.priceOracleAddress).poolSize(self)
    tradeFee *= output_token_price / TOKEN_PRICE_MULTIPLIER
    ownerFee *= output_token_price / TOKEN_PRICE_MULTIPLIER
    new_owner_shares: uint256 = self.totalSupply * ownerFee / (pool_size + tradeFee)

    token_divider: uint256 = 10**(self.decimals - ERC20(output_token).decimals())
    output_amount = output_amount / token_divider
    assert output_amount >= min_output_amount

    ERC20(input_token).transferFrom(msg.sender, self, input_amount)
    ERC20(output_token).transfer(msg.sender, output_amount)
    log.Trade(input_token, output_token, input_amount)

    self.balances[self.owner] += new_owner_shares
    self.totalSupply += new_owner_shares

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
def updateFee(fee_name: bytes[32], value: decimal) -> bool:
    assert msg.sender == self.owner
    self.feesInt[fee_name] = convert(convert(floor(value * 1000.0), uint256), int128)
    log.FeeUpdated(fee_name, value)
    return True

@public
@constant
def fees(fee_name: bytes[32]) -> decimal:
    return convert(self.feesInt[fee_name], decimal) / 1000.0

@public
def updatePriceOracleAddress(new_address: address) -> bool:
    assert msg.sender == self.owner
    self.priceOracleAddress = new_address
    log.PriceOracleAddressUpdated(new_address)
    return True

# ERC-20 functions

@public
@constant
def balanceOf(_owner: address) -> uint256:
    return self.balances[_owner]

@public
def transfer(_to: address, _value: uint256) -> bool:
    self.balances[msg.sender] -= _value
    self.balances[_to] += _value
    log.Transfer(msg.sender, _to, _value)
    return True

@public
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    self.balances[_from] -= _value
    self.balances[_to] += _value
    self.allowances[_from][msg.sender] -= _value
    log.Transfer(_from, _to, _value)
    return True

@public
def approve(_spender: address, _value: uint256) -> bool:
    self.allowances[msg.sender][_spender] = _value
    log.Approval(msg.sender, msg.sender, _value)
    return True

@public
@constant
def allowance(_owner: address, _spender: address) -> uint256:
    return self.allowances[_owner][_spender]
