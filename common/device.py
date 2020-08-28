import time

class Device():
  def __init__ (self, device):
    self.address = device['Address']
    self.addressType = device['AddressType']
    self.connectionPeriod = device["ConnectionPeriod"]
    self.lastTimeConnected = device["LastTimeConnected"]
    self.setNextTimeToConnect()
  
  def setNextTimeToConnect(self):
    rightNow= time.time() 
    marginSafety = 10 # seconds
    multiplicator= int( [(rightNow+marginSafety) - self.lastTimeConnected]/self.connectionPeriod )
    self.nextTimeToConnect = self.lastTimeConnected + (multiplicator+1) * self.connectionPeriod
