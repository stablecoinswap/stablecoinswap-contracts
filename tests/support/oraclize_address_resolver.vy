# THIS CONTRACT IS FOR TESTING PURPOSES AND IS NOT PART OF THE PROJECT

addr: public(address)
owner: address

@public
def __init__():
    self.owner = msg.sender

@public
def changeOwner(newowner: address):
    assert self.owner == msg.sender
    self.owner = newowner

@public
@constant
def getAddress() -> address:
    return self.addr

@public
def setAddr(newaddr: address):
    assert self.owner == msg.sender
    self.addr = newaddr
