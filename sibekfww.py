import re,zlib,subprocess,time,argparse
from fw import SibekFW
from fwusb import SibekFWUSB

class SibekFWManager(SibekFW):

  info = ""
  fw = None

  def __init__(self,fw):
    self.fw = fw

  def __del__(self):
    self.disconnect()

  def getinfo(self):
    self.info = self.communicate("info").strip()

  def getmode(self):
    p = re.compile("^([A-Z]+)\smode")
    res = p.findall(self.info)[0]
    return(res)

  def getname(self):
    p = re.compile("([a-zA-Z0-9\-]*).*ver")
    res = p.findall(self.info)[0]                                                                                                                                                    
    return(res)

  def getver(self):
    p = re.compile("ver\.\s([\d\.]+)")                                                                                                                                         
    res = p.findall(self.info)[0]
    return(res)

  def cksum(self,filename):
    p = subprocess.Popen("cksum {}".format(filename),shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)                                                     
    out = p.communicate()
    while p.poll() is None:
      time.sleep(0.5)  
    if( p.poll() == 0):
      return(out[0])
    else:
      print("Unexpected error: Normalize with sox return an error")
      exit(1)

  def communicate(self,str,timeout=1):
    return self.fw.communicate(str,timeout=1)

  def connect(self,device=0):
    return self.fw.connect(device)

  def disconnect(self):
    return self.fw.disconnect()

  def write(self,str):
    return self.fw.write(str)

  def writeb(self,str):
    return self.fw.writeb(str)

  def read(self):
    return self.fw.read()

  def readb(self):
    return self.fw.readb()
  
  def communicate(self,str,timeout=1):
    return(self.fw.communicate(str,timeout))

  def sendfile(self,filename,data):
    mes = self.communicate("cat< {} {}".format(filename,len(data)))
    if(mes == "Ready to file receiveance..."):
      self.writeb(data)
      mes = self.read()
      if( mes == "file received" ):
        return(0)
      else:
        print(mes)
        return(1)
    else:
      print(mes)
      return(1)

  def receivefile(self,filename):
    self.write("cat> {}".format(filename))
    return(self.readb())

parser = argparse.ArgumentParser()
parser.add_argument('-l', help='list usb devices', action="store_true")
parser.add_argument('-f', help='firmware source file, ex. fware.hex', metavar="filename", dest="filename")
parser.add_argument('-t', choices=['usb', 'ssh'], default='usb', help='connection type (usb,ssh), default: usb', required=False, metavar="contype", dest="contype")
parser.add_argument('-d', help='USB: Device number, SSH: ip address', metavar="dest", dest="dest")
parser.add_argument('-u', help='user for ssh', metavar="user", dest="user")
parser.add_argument('-p', help='password for ssh', metavar="pass", dest="pass")
parser.add_argument('--ls', help='list files on device', action="store_true")

parser.add_argument('-df', metavar="filename", help='Download file')
parser.add_argument('-uf', metavar="filename", help='Upload file')

args = parser.parse_args()

if( args.l ):
  fw = SibekFWUSB()
  fw.listusb()
  exit(0)

if( args.contype == "usb" ):
  dest = 0
  fw = SibekFWUSB()
  fw.listusb()
  print("")
  if( len(fw.usblist) > 1 ):
    if( not args.dest is None ):
      args.dest = int(args.dest)
      if( (args.dest > 0) and (args.dest <= len(fw.usblist)) ):
        dest = (args.dest-1)
      else:
        fw.listusb()
        print("\nThere is more than one usb device, you should use option -d to specify one from the list abowe")
        exit(1)
    else:
      fw.listusb() 
      print("\nThere is more than one usb device, you should use option -d to specify one from the list abowe")
      exit(1)
  if( len(fw.usblist) == 0 ):
    print("No devices detected")
    exit(0)

if( args.contype == "ssh" ):
  print("Not implemented yet.")
  exit(0)

fwm = SibekFWManager(fw)  

try:
  fwm.connect(dest)
except:
  print("Can't connect to device")
  raise

fwm.getinfo()

print("Found device:")
print("{}\n".format(fwm.info))

if( args.ls ):
  print(fwm.communicate("ls"))
  exit(0)

if( not args.uf is None):
  filename = args.uf
  try:
    f = open(filename,'rb')
    data = f.read()
    f.close()
  except:
    print("Can't read file: {}".format(filename))
    raise
  if(not fwm.sendfile(filename,data) ):
    print("File {} sent successfully".format(filename))
    exit(0)
  else:
    print("Can't send file")
    exit(1)

if( not args.df is None):
  filename = args.df
  try:   
    f = open(filename,'wb')
  except:
    print("Can't open file: {}".format(filename))
    raise
  data = fwm.receivefile(filename)
  f.write(data)
  f.close
  print("File {} received".format(filename))
  exit(0)

if( not args.filename is None ):
  filename = args.filename
else:
  print("sibekfww.py: error: argument -f is required")
  exit(1)

try:
  f = open(filename,'rb')
  data = f.read()
  f.close()
except:
  print("Can't read file: {}".format(filename))
  raise

#Flashing
startmode = fwm.getmode()

#Check LOADER Mode
if( not fwm.getmode() == "LOADER" ):
  print("Switching to LOADER mode..."),
  fwm.communicate("softpart")
  fwm.disconnect()
  time.sleep(3)
  try:
    fwm.connect()
  except:
    time.sleep(5)
    try:
      fwm.connect()
    except:
      print("\nCan't connect to device while swithing to loader mode")
      raise
  fwm.getinfo()

if( not fwm.getmode() == "LOADER" ):
  print("\nCan't switch to loader mode. You can try do it mannualy by softpart command")
  exit(1)

if(not startmode == "LOADER"):
  print("OK\n")
  print("Found device:")
  print("{}\n".format(fwm.info))


print("Sending fware.hex..."),
if ( fwm.sendfile("fware.hex",data) ):
  print("error")
  print("Can't send file to device")
  exit(1)
print("OK")
  
crc = fwm.cksum(filename)

print("Sending fware.crc..."),
if ( fwm.sendfile("fware.crc",crc) ):
  print("error")
  print("Can't send file to device")
  exit(1)
print("OK")

print(fwm.communicate("writehware",10))
