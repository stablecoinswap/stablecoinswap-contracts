contract ERC20():
    def transfer(_to: address, _value: uint256) -> bool: modifying
    def transferFrom(_from: address, _to: address, _value: uint256) -> bool: modifying
    def allowance(_owner: address, _spender: address) -> uint256: constant
    def approve(_spender: address, _value: uint256) -> bool: modifying
    
contract Stablecoinswap():
    def tokenExchangeRateAfterFees (input_token_address: address, output_token_address: address) -> uint256: constant
    def swapTokens(input_token: address, output_token: address, erc20_input_amount: uint256, erc20_min_output_amount: uint256, deadline: timestamp) -> uint256: modifying

FEE_MULTIPLIER: constant(uint256) = 100000
EXCHANGE_RATE_MULTIPLIER: constant(uint256) = 10000000000000000000000 #10**22

# Events
OwnershipTransferred: event({previous_owner: indexed(address), new_owner: indexed(address)})
Trade: event({input_token: indexed(address), output_token: indexed(address), input_amount: indexed(uint256)})
FeeUpdated: event({value: indexed(decimal)})

name: public(string[32])               # StablecoinswapProxy
stablecoinswapAddress: public(address) # main contract
owner: public(address)                 # contract owner
feeInt: public(uint256)                # fee multiplied by FEE_MULTIPLIER

@public
def __init__(stablecoinswap_addr: address):
    self.owner = msg.sender
    self.name = "StablecoinswapProxy"
    self.stablecoinswapAddress = stablecoinswap_addr
    self.feeInt = 250

@public
@constant
def fee() -> decimal:
    return convert(self.feeInt, decimal) / convert(FEE_MULTIPLIER, decimal)
    
# Note that due to rounding, the fees could be slightly higher for the tokens with smaller decimal precision.
@public
@constant
def tokenExchangeRateAfterFees(input_token_address: address, output_token_address: address) -> uint256:
    stablecoinswap_rate: uint256 = Stablecoinswap(self.stablecoinswapAddress).tokenExchangeRateAfterFees(input_token_address, output_token_address)
    multiplier_after_fee: uint256 = FEE_MULTIPLIER - self.feeInt
    exchange_rate: uint256 = stablecoinswap_rate * multiplier_after_fee / FEE_MULTIPLIER
    return exchange_rate

@public
@constant
def tokenOutputAmountAfterFees(input_token_amount: uint256, input_token_address: address, output_token_address: address) -> uint256:
    # we can't just multiply all fees here because we round fee up
    multiplier_after_fee: uint256 = FEE_MULTIPLIER - self.feeInt
    input_amount_after_fee: uint256 = input_token_amount * multiplier_after_fee / FEE_MULTIPLIER
    stablecoinswap_rate: uint256 = Stablecoinswap(self.stablecoinswapAddress).tokenExchangeRateAfterFees(input_token_address, output_token_address)

    output_token_amount: uint256 = input_amount_after_fee * stablecoinswap_rate / EXCHANGE_RATE_MULTIPLIER
    return output_token_amount

# Trade one erc20 token for another
@public
@nonreentrant('lock')
def swapTokens(input_token: address, output_token: address, erc20_input_amount: uint256, erc20_min_output_amount: uint256, deadline: timestamp) -> uint256:
    transfer_from_user_result: bool = ERC20(input_token).transferFrom(msg.sender, self, erc20_input_amount)
    assert transfer_from_user_result

    multiplier_after_fee: uint256 = FEE_MULTIPLIER - self.feeInt
    input_amount_after_fee: uint256 = erc20_input_amount * multiplier_after_fee / FEE_MULTIPLIER
    fee_amount: uint256 = erc20_input_amount - input_amount_after_fee

    # set allowance if necessary
    stablecoinswap_allowance: uint256 = ERC20(input_token).allowance(self, self.stablecoinswapAddress)
    if (stablecoinswap_allowance < input_amount_after_fee):
        approval_result: bool = ERC20(input_token).approve(self.stablecoinswapAddress, 10**32)
        assert approval_result

    erc20_output_amount: uint256 = Stablecoinswap(self.stablecoinswapAddress).swapTokens(input_token, output_token, input_amount_after_fee, erc20_min_output_amount, deadline)
    transfer_result: bool = ERC20(output_token).transfer(msg.sender, erc20_output_amount)
    assert transfer_result
    log.Trade(input_token, output_token, erc20_input_amount)
    return erc20_output_amount

@public
def transferOwnership(new_owner: address) -> bool:
    assert new_owner != ZERO_ADDRESS
    assert msg.sender == self.owner
    self.owner = new_owner
    log.OwnershipTransferred(self.owner, new_owner)
    return True

@public
def updateFee(value: decimal) -> bool:
    assert msg.sender == self.owner
    self.feeInt = convert(floor(value * convert(FEE_MULTIPLIER, decimal)), uint256)
    log.FeeUpdated(value)
    return True

@public
def withdrawFee(token_address: address, amount: uint256) -> bool:
    assert msg.sender == self.owner
    transfer_result: bool = ERC20(token_address).transfer(msg.sender, amount)
    assert transfer_result
    return True
