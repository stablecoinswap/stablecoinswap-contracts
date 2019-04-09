PriceUpdated: event({token_address: indexed(address), new_price: indexed(uint256)})

name: public(string[16])
owner: address
tokens: public(map(address, uint256))

@public
def __init__():
    self.owner = msg.sender
    self.name = 'PriceOracle'

@public
# we set token price as uint256:
# token_price = usd_price * 10**8
# example: USD price for DAI = $0.97734655, usd price = 97734655
def updatePrice(token_address: address, usd_price: uint256):
    assert msg.sender == self.owner
    self.tokens[token_address] = usd_price
    log.PriceUpdated(token_address, usd_price)
