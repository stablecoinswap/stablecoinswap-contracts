struct PriceInfo:
    price: uint256
    lastUpdate: uint256

price: public(uint256)
lastUpdate: public(uint256)
owner: public(address)
name: public(string[16])

@public
def __init__():
    self.owner = msg.sender
    self.name = 'DaiPriceOracle'

@public
@constant
def g_priceInfo() -> PriceInfo:
    pi: PriceInfo = PriceInfo({price: self.price, lastUpdate: self.lastUpdate})
    return pi

@public
def updatePrice(_price: uint256) -> PriceInfo:
    assert msg.sender == self.owner
    self.price = _price
    self.lastUpdate = block.number
    pi: PriceInfo = PriceInfo({price: self.price, lastUpdate: self.lastUpdate})
    return pi
