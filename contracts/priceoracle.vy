contract ERC20():
    def balanceOf(_owner: address) -> uint256: constant
    def decimals() -> uint256: constant

MIN_PRICE: constant(uint256) = 1000000 # $0.01
MAX_PRICE: constant(uint256) = 10000000000 # $100
PRICE_MULTIPLIER: constant(uint256) = 100000000

PriceUpdated: event({token_address: indexed(address), new_price: indexed(uint256)})
TokenAddressUpdated: event({token_address: indexed(address), token_index: indexed(int128)})

name: public(string[16])
owner: address
supported_tokens: public(address[5])
token_prices: public(map(address, uint256))

@public
def __init__():
    self.owner = msg.sender
    self.name = 'PriceOracle'

@public
@constant
def poolSize(contract_address: address) -> uint256:
    token_address: address
    total: uint256 = 0
    amount: uint256 = 0
    for ind in range(5):
        token_address = self.supported_tokens[ind]
        if token_address != ZERO_ADDRESS:
            total += ERC20(token_address).balanceOf(contract_address) * 10**(18 - ERC20(token_address).decimals()) * self.token_prices[token_address] / PRICE_MULTIPLIER
    return total

@public
def updateTokenAddress(token_address: address, ind: int128):
    assert msg.sender == self.owner
    self.supported_tokens[ind] = token_address
    log.TokenAddressUpdated(token_address, ind)

@public
# we set token price as uint256:
# token_price = usd_price * 10**8
# example: USD price for DAI = $0.97734655, usd price = 97734655
def updatePrice(token_address: address, usd_price: uint256):
    assert msg.sender == self.owner
    assert MIN_PRICE <= usd_price and usd_price <= MAX_PRICE
    self.token_prices[token_address] = usd_price
    log.PriceUpdated(token_address, usd_price)
