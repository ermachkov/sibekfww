import serial,sys,subprocess,re
from serial.tools import list_ports
from fw import SibekFW

class SibekFWUSB(SibekFW):
  
  ser = serial.Serial
  usblist = []

  vid = ["0483"]
  pid = ["5740"]

  def __init__(self):
    self.findusb()

  # OK = device, 1 - error
  def finddevice(self,vid,pid):
    p = re.compile("USB\sVID\:PID={}\:{}".format(vid,pid), re.IGNORECASE)
    for port in list_ports.comports():
      if( p.match(port[2]) ):
        return(port[0])
    return(1)

  # 0 - OK, 1 - not found, 2 - error
  def findusb(self):
    self.usblist = []
    p = subprocess.Popen("lsusb",shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)                                                     
    out = p.communicate()
    while p.poll() is None:
      time.sleep(0.5)  
    if( p.poll() == 0):
      out = out[0]
      p = re.compile("([a-f\d]{4})\:([a-f\d]{4})(.*)")
      res = p.findall(out)
      for r in res:
        if (r[0] in self.vid):
          if(r[1] in self.pid):
            self.usblist.append((r[0],r[1],r[2].strip(),self.finddevice(r[0],r[1])))
            return(0)
      return(1)
    else:
      return(2)

  def listusb(self):
    print("Device list: ")
    i = 0
    for usb in self.usblist:
      i += 1
      print("{}. {}:{} {} {}".format(i,usb[0],usb[1],usb[2],usb[3]))

  def connect(self,device=0):
    #TODO: already connected test, reconnection if trouble
    self.ser = serial.Serial(self.usblist[device][3], 115200, timeout=1)
    return(0)

  def disconnect(self):
    #TODO: connection test
    self.ser.close()
    return(0)

  def write(self,str):
    w = self.ser.write("{}\n".format(str))
    self.ser.flush()
    return(w)

  def writeb(self,bin):
    w = self.ser.write(bin)
    self.ser.flush()
    return(w)

  def read(self):
    i = 0
    mes = ""
    while(1):
      try:
        a = self.ser.read(1)
      except:
        return(mes)
      mes += a
      if( a.encode('hex') == '0d' or a.encode('hex') == '0a'): i += 1
      else: i = 0
      if( i==4 ):
        break
      elif(a == ''): break
    return(mes.strip())

  def readb(self):
    i = 0
    mes = ""
    while(1):
      try:
        a = self.ser.read(1)
      except:
        return(mes)
      mes += a
      if(a == ''): break
    return(mes)

  def communicate(self,str,timeout=1):
    self.ser.timeout = timeout
    self.write(str)
    return(self.read())
