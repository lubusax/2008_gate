import os

def setDirectories(basisDir):
  dataDir = basisDir + "/data"
  os.environ["DATA_DIR"] = dataDir
  #print(os.environ.get('DATA_DIR', None))
  commonDir= basisDir + "/common"
  os.environ["COMMON_DIR"] = commonDir