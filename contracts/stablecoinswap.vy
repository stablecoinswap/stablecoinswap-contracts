struct QueryData:
    input_token: address
    output_token: address
    user_address: address
    input_amount: uint256
    min_output_amount: uint256

contract ERC20():
    def transfer(_to: address, _value: uint256) -> bool: modifying
    def transferFrom(_from: address, _to: address, _value: uint256) -> bool: modifying
    def balanceOf(_owner: address) -> uint256: constant
    def allowance(_owner: address, _spender: address) -> uint256: constant

contract OraclizeI():
    def getPrice(_datasource: string[20]) -> uint256: constant
    def query2(_timestamp: timestamp, _datasource: string[20], _arg1: string[100], _arg2: string[160]) -> bytes32: modifying

contract OraclizeAddrResolverI():
    def getAddress() -> address: constant

# ERC20 events
Transfer: event({_from: indexed(address), _to: indexed(address), _value: uint256})
Approval: event({_owner: indexed(address), _spender: indexed(address), _value: uint256})

OwnershipTransferred: event({previous_owner: indexed(address), new_owner: indexed(address)})
LiquidityAdded: event({provider: indexed(address), amount: indexed(uint256)})
LiquidityRemoved: event({provider: indexed(address), amount: indexed(uint256)})
Trade: event({input_token: indexed(address), output_token: indexed(address), input_amount: indexed(uint256)})
PermissionUpdated: event({name: indexed(bytes[32]), value: indexed(bool)})
FeeUpdated: event({name: indexed(bytes[32]), value: indexed(decimal)})
TokenPriceOracleUrlUpdated: event({new_url: indexed(string[64])})
OraclizeAddressUpdated: event({new_address: indexed(address)})
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
fees: public(map(bytes[32], decimal))             # trade / pool fees
tokenPriceOracleUrl: string[64]                   # oracle url to get token prices
oraclizeAddress: public(address)                  # address of oraclize contract
pendingQueries: map(bytes32, QueryData)           # queries waiting for answer from oracle
oraclizeOwner: address                            # address of oraclize contract creator

@public
def __init__(token_addresses: address[3], oracle_url: string[64], oraclize_addr: address, oraclize_owner: address):
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

    self.fees['tradeFee'] = 0.002
    self.fees['poolFee'] = 0.001

    self.tokenPriceOracleUrl = oracle_url
    # mainnet oraclize_addr - 0x1d3B2638a7cC9f2CB3D298A3DA7a90B67E5506ed
    self.oraclizeAddress = OraclizeAddrResolverI(oraclize_addr).getAddress()
    self.oraclizeOwner = oraclize_owner

# Deposit stablecoins.
@public
def addLiquidity(token_address: address, amount: uint256, deadline: timestamp) -> bool:
    assert self.inputTokens[token_address]
    assert deadline > block.timestamp and amount > 0
    assert self.permissions["liquidityAddingAllowed"]
    assert ERC20(token_address).balanceOf(msg.sender) >= amount
    assert ERC20(token_address).allowance(msg.sender, self) >= amount

    if self.totalSupply > 0:
        self.balances[msg.sender] += amount
        self.totalSupply += amount
    else:
        assert amount >= 1000000000
        self.balances[msg.sender] = amount
        self.totalSupply = amount

    ERC20(token_address).transferFrom(msg.sender, self, amount)
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
    ERC20(token_address).transfer(msg.sender, amount)
    log.LiquidityRemoved(msg.sender, amount)
    return True

@public
def stringToNumber(s: string[32]) -> uint256:
    result: uint256
    num: uint256
    digit: uint256

    num = convert(convert(s, bytes[32]), uint256)
    for i in range(32):
        if i < len(s):
            digit = num % 256 - 48
            num = num / 256
            result = result + digit * convert(10**i, uint256)
    return result

@public
def addressToString(addr: address) -> string[42]:
    # we need to convert hexadecimal values like 0x9C to their string values - '9C'
    # so we convert hexadecimal to integer value, then split it to digits: for value above they are 9 and 12 (0xC)
    # after this we replace digits with their symbols: digits[9] - '9', digits[12] - 'C'
    digits: bytes[16] = convert('0123456789ABCDEF', bytes[16])
    address_bytes: bytes32 = convert(addr, bytes32)
    chunks: bytes[2][20]
    result: bytes[42]
    c: int128
    d1: int128
    d2: int128

    for i in range(20):
        c = convert(slice(address_bytes, start=i+12, len=1), int128)
        d1 = c / 16
        d2 = c % 16
        chunks[i] = concat(slice(digits, start=d1, len=1), slice(digits, start=d2, len=1))
    result = concat(b'0x', chunks[0], chunks[1], chunks[2], chunks[3], chunks[4], chunks[5], chunks[6], chunks[7], chunks[8], chunks[9], chunks[10], chunks[11], chunks[12], chunks[13], chunks[14], chunks[15], chunks[16], chunks[17], chunks[18], chunks[19])

    return convert(result, string[42])

# get response with price from oracle and swap tokens
@public
def __callback(myid: bytes32, oracle_str: string[32]):
    assert msg.sender == self.oraclizeOwner
    assert self.pendingQueries[myid].input_token != ZERO_ADDRESS

    current_price: uint256 = self.stringToNumber(oracle_str)
    fee_numerator: int128 = 1000 - floor(self.fees['tradeFee'] * 1000.0)
    output_amount: uint256 = self.pendingQueries[myid].input_amount * current_price / 1000000 * convert(fee_numerator, uint256) / 1000
    assert output_amount >= self.pendingQueries[myid].min_output_amount

    ERC20(self.pendingQueries[myid].input_token).transferFrom(self.pendingQueries[myid].user_address, self, self.pendingQueries[myid].input_amount)
    ERC20(self.pendingQueries[myid].output_token).transfer(self.pendingQueries[myid].user_address, output_amount)

    log.Trade(self.pendingQueries[myid].input_token, self.pendingQueries[myid].output_token, self.pendingQueries[myid].input_amount)
    clear(self.pendingQueries[myid])

@public
def createOracleParamsString(input_token: address, output_token: address) -> string[160]:
    str: string[160] = concat('{"base_token_address":"', self.addressToString(input_token), '", "quote_token_address":"', self.addressToString(output_token), '"}')
    return str

# Trade one stablecoin for another
@public
def swapTokens(input_token: address, output_token: address, input_amount: uint256, min_output_amount: uint256, deadline: timestamp) -> bool:
    assert self.inputTokens[input_token] and self.outputTokens[output_token]
    assert input_amount > 0 and min_output_amount > 0
    assert deadline > block.timestamp
    assert self.permissions["tradingAllowed"]
    assert ERC20(input_token).balanceOf(msg.sender) >= input_amount
    assert ERC20(input_token).allowance(msg.sender, self) >= input_amount

    query_price: uint256(wei) = OraclizeI(self.oraclizeAddress).getPrice('URL')
    assert query_price <= self.balance
    assert query_price <= as_wei_value(1, 'ether') # unexpectedly high price

    queryId: bytes32
    if query_price > 0:
        queryId = OraclizeI(self.oraclizeAddress).query2(block.timestamp, 'URL', self.tokenPriceOracleUrl, self.createOracleParamsString(input_token, output_token), value=query_price)
    else:
        queryId = OraclizeI(self.oraclizeAddress).query2(block.timestamp, 'URL', self.tokenPriceOracleUrl, self.createOracleParamsString(input_token, output_token))
    self.pendingQueries[queryId] = QueryData({input_token: input_token, output_token: output_token, user_address: msg.sender, input_amount: input_amount, min_output_amount: min_output_amount})

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
    self.fees[fee_name] = value
    log.FeeUpdated(fee_name, value)
    return True

@public
def updateTokenPriceOracleUrl(url: string[64]) -> bool:
    assert msg.sender == self.owner
    self.tokenPriceOracleUrl = url
    log.TokenPriceOracleUrlUpdated(self.tokenPriceOracleUrl)
    return True

@public
def updateOraclizeAddress(new_address: address) -> bool:
    assert msg.sender == self.owner
    self.oraclizeAddress = new_address
    log.OraclizeAddressUpdated(self.oraclizeAddress)
    return True

@public
@payable
def __default__():
    log.Payment(msg.value, msg.sender)

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
