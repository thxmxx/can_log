import sys
import time
import serial
import struct
import logging
import Colorer
import argparse
from socket import socket, AF_INET, SOCK_DGRAM
import threading
import json

USART_FRAMECTRL = 0xA5                                                  
USART_FRAMEHEAD = 0xAA
USART_FRAMETAIL = 0x55

def insertCtrl(buffer, ch):
    result = buffer
    #print("insertCtrl ch={:02x}".format(ch))
    if (ch == USART_FRAMECTRL or ch == USART_FRAMEHEAD or ch == USART_FRAMETAIL):
        result.append(USART_FRAMECTRL)
    return result

def setTransmitMsg(id, rtr, ext, len, buf):
    #sendData = [0xAA, 0xAA, 0x78, 0x56, 0x34, 0x12, 0x11, 0x22, 0x33, 0x44, 0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x3F, 0x55, 0x55, 0xF0]
    #print("sendData={}".format(sendData))

    sendData = [0xAA, 0xAA]
    idStr = "{:08x}".format(id)
    logging.debug("idStr={}".format(idStr))
    crc = 0
    if (ext == 0):
        id = int(idStr[6:8],16)
        sendData = insertCtrl(sendData, id)
        sendData.append(id)
        crc = crc + id
        id = int(idStr[4:6],16) & 0x7
        sendData = insertCtrl(sendData, id)
        sendData.append(id)
        crc = crc + id
        sendData.append(0)
        sendData.append(0)
        logging.debug("id={:02x}{:02x}".format(sendData[2], sendData[3]))
    else:
        id = int(idStr[6:8],16)
        sendData = insertCtrl(sendData, id)
        sendData.append(id)
        crc = crc + id
        id = int(idStr[4:6],16)
        sendData = insertCtrl(sendData, id)
        sendData.append(id)
        crc = crc + id
        id = int(idStr[2:4],16)
        sendData = insertCtrl(sendData, id)
        sendData.append(id)
        crc = crc + id
        id = int(idStr[0:2],16) & 0x1F
        sendData = insertCtrl(sendData, id)
        sendData.append(id)
        crc = crc + id
        logging.debug("id={:02x}{:02x}".format(sendData[2], sendData[3]))
    for x in range(len):
        sendData = insertCtrl(sendData, buf[x])
        sendData.append(buf[x])
        crc = crc + buf[x]
    if (len < 8):
        for x in range(8-len):
            sendData.append(0)
    sendData.append(len) # Frame Data Length
    crc = crc + len
    sendData.append(0)
    sendData.append(ext) # Standard/Extended frame
    crc = crc + ext
    sendData.append(rtr) # Data/Request frame
    crc = crc + rtr
    crc = crc & 0xff
    logging.debug("crc={:2x}".format(crc))
    sendData = insertCtrl(sendData, crc)
    sendData.append(crc)
    sendData.append(0x55)
    sendData.append(0x55)
    #sendData.append(0xF0)
    logging.debug("sendData={}".format(sendData))
    return sendData

# https://qiita.com/mml/items/ccc66ecc46d8299b3346
def sendMsg( buf ):
      while True:
            if ser.out_waiting == 0:
                  break
      for b in buf:
            a = struct.pack( "B", b )
            ser.write(a)
      ser.flush()
         
def initId():
    data = [0xAA, 0xAA, 0xFF, 0xFE, 0xFF, 0x01, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x08, 0xFF, 0x01, 0x00, 0x66, 0x55, 0x55]

    data[18]=sum(data[2:18]) & 0xFF
    #print("data[18]={:02x}".format(data[18]))
    sendMsg(data)

def readInfo(id):
    data = [0xAA, 0xAA, 0xE0, 0xFF, 0xFF, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x01, 0x01, 0x66, 0x55, 0x55]
    idStr = "{:08x}".format(id)
    #print("idStr={}".format(idStr))
    data[2] = int(idStr[6:8],16)
    data[3] = int(idStr[4:6],16)
    data[4] = int(idStr[2:4],16)
    data[5] = int(idStr[0:2],16)
    data[18]=sum(data[2:18]) & 0xFF
    #print("data={:02x}{:02x}{:02x}{:02x}".format(data[2], data[3], data[4], data[5]))
    sendMsg(data)
     
def readFilter(index):
     data = [0xAA, 0xAA, 0xE0, 0xFE, 0xFF, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x01, 0x01, 0x66, 0x55, 0x55]

     #print("index={}".format(index))
     data[2] = 0xE0 + index
     data[18]=sum(data[2:18]) & 0xFF
     #print("data4[18]={:2x}".format(data4[18]))
     sendMsg(data)

def setSpeed(speed):
     logging.info("speed={}".format(speed))
     speed1000 = [0xAA, 0xAA, 0xD0, 0xFE, 0xFF, 0x01, 0x40, 0x42, 0x0F, 0x00, 0x01, 0x02, 0x00, 0x00, 0x04, 0xFF, 0x01, 0x00, 0x66, 0x55, 0x55]

     speed800 = [0xAA, 0xAA, 0xD0, 0xFE, 0xFF, 0x01, 0x00, 0x35, 0x0C, 0x00, 0x01, 0x02, 0x00, 0x00, 0x04, 0xFF, 0x01, 0x00, 0x16, 0x55, 0x55]

     speed500 = [0xAA, 0xAA, 0xD0, 0xFE, 0xFF, 0x01, 0x20, 0xA1, 0x07, 0x00, 0x01, 0x02, 0x00, 0x00, 0x04, 0xFF, 0x01, 0x00, 0x9D, 0x55, 0x55]

     speed400 = [0xAA, 0xAA, 0xD0, 0xFE, 0xFF, 0x01, 0x80, 0x1A, 0x06, 0x00, 0x01, 0x02, 0x00, 0x00, 0x04, 0xFF, 0x01, 0x00, 0x75, 0x55, 0x55]

     speed250 = [0xAA, 0xAA, 0xD0, 0xFE, 0xFF, 0x01, 0x90, 0xD0, 0x03, 0x00, 0x01, 0x02, 0x00, 0x00, 0x04, 0xFF, 0x01, 0x00, 0x38, 0x55, 0x55]

     speed125 = [0xAA, 0xAA, 0xD0, 0xFE, 0xFF, 0x01, 0x48, 0xE8, 0x01, 0x00, 0x01, 0x02, 0x00, 0x00, 0x04, 0xFF, 0x01, 0x00, 0x06, 0x55, 0x55]

     speed100 = [0xAA, 0xAA, 0xD0, 0xFE, 0xFF, 0x01, 0xA0, 0x86, 0x01, 0x00, 0x01, 0x02, 0x00, 0x00, 0x04, 0xFF, 0x01, 0x00, 0xFC, 0x55, 0x55]


     if (speed == 1000000):
         sendMsg(speed1000)
         return True
     elif (speed == 800000):
         sendMsg(speed800)
         return True
     elif (speed == 500000):
         sendMsg(speed500)
         return True
     elif (speed == 400000):
         sendMsg(speed400)
         return True
     elif (speed == 250000):
         sendMsg(speed250)
         return True
     elif (speed == 125000):
         sendMsg(speed125)
         return True
     elif (speed == 100000):
         sendMsg(speed100)
         return True
     else:
         return False
   
format="%(asctime)s [%(filename)s:%(lineno)d] %(levelname)-8s %(message)s"

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", help="open port")
parser.add_argument("-s", "--speed", help="can bit rate", type=int)
parser.add_argument("-u", "--udp", help="UDP receive port", type=int)
parser.add_argument("-l", "--log", dest="logLevel", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Set the logging level")
parser.add_argument("-i", "--input", dest="inputLog", help="Input logFile")

args = parser.parse_args()
device = "/dev/ttyACM0"
speed = 500000
udpPort = 8200

if args.port:
    print("args.port={}".format(args.port))
    device = args.port
if args.speed:
    print("args.speed={}".format(args.speed))
    speed = args.speed
if args.udp:
    print("args.udp={}".format(args.udp))
    udpPort = args.udp
if args.logLevel:
    level=getattr(logging, args.logLevel)
    print("logLevel set to {}".format(level))
    #logging.basicConfig(level=getattr(logging, args.logLevel))
    logging.basicConfig(level=getattr(logging, args.logLevel), format=format)
else:
    print("logLevel set to {}".format(logging.WARNING))
    logging.basicConfig(level=logging.WARNING, format=format)

if (speed != 1000000 and speed != 500000 and speed != 400000 and speed != 250000 and speed != 125000 and speed != 100000):
    logging.error("This speed {} is not supported.".format(speed))
    sys.exit()

ser = serial.Serial(
      port = device,
      baudrate = 115200,
      #parity = serial.PARITY_NONE,
      #bytesize = serial.EIGHTBITS,
      #stopbits = serial.STOPBITS_ONE,
      #timeout = None,
      #xonxoff = 0,
      #rtscts = 0,
      )

log_file = open(args.inputLog, 'r')
log_lines = log_file.readlines()

frameId = 1

while True:
    # 0x0CFE6C01#8#433FFFC000FE4C06
    for log_line in log_lines:
        ts = log_line.split()[0]
        data = log_line.split()[1]
        print(data)
        frameId = int(data.split('#')[0], base=16)
        # frameId = 0x0CFE6C01
        frameRequest = 0
        frameType = 1
        frameLength = int(data.split('#')[1])
        # frameData = [0x43, 0x3F, 0xFF, 0xC0, 0x00, 0xFE, 0x4C, 0x06]
        frameData = list(bytearray.fromhex(data.split('#')[2]))
        sendData = setTransmitMsg(frameId, frameRequest, frameType, frameLength, frameData)
        sendMsg(sendData)
        print("frameId={0} sendData={1}".format(hex(frameId), sendData))
        time.sleep(0.01)


# frameId += 1
# frameRequest = 0
# frameType = 1
# frameLength = 8
# frameData = [0x43, 0x3F, 0xFF, 0xC0, 0x00, 0xFE, 0x4C, 0x06]
# sendData = setTransmitMsg(frameId, frameRequest, frameType, frameLength, frameData)
# sendMsg(sendData)
# print("frameId={0} sendData={1}".format(hex(frameId), sendData))