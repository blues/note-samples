defaultProductUID = 'com.my.product.uid'
defaultHubHost    = "a.notefile.net"
defaultDebugFlag  = False
defaultPortType   = "i2c"
defaultPortName   = "/dev/i2c-1"
defaultBaudRate   = 9600
gpioAttnPin = 6 # info: https://dev.blues.io/hardware/notecarrier-datasheet/notecarrier-pi/#dip-switches
remoteCommandQueue = "commands.qi"
testAttnResponseQueue = "test.qo"

import os
import notecard
import logging
import RPi.GPIO as GPIO
import sys
import signal
from multiprocessing import Lock



try: 
    from periphery import I2C
except:
    pass

import serial

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)




def configureNotecard(card, productUID=defaultProductUID,host=defaultHubHost):
  
    dataUplinkPeriodMinutes = 1
    dataDownlinkPeriodMinutes = 2

    req = {"req": "hub.set",
            "product":productUID,
            "host":host,
            "mode":"continuous",
            "outbound":dataUplinkPeriodMinutes,
            "inbound":dataDownlinkPeriodMinutes,
            "sync":True,
            "align":True
    }

    card.Transaction(req) 

def count(args):
    n = args["min"] if "min" in args else 0
    inc = args["inc"] if "inc" in args else 1
    m = args["max"] if "max" in args else 10
    log.info("start counter")
    while n <= m:
        log.info(f"count value: {n}")
        n += inc
    

commandMap = {"print": print, "count": count}

taskList = []
taskMutex = Lock()
def addTask(f, a):
    taskList.append((f,a))

def executeTask(t):
    f = t[0]
    a = t[1]
    f(a)

def enqueueCommands(card):
    
    req = {"req":"note.get","file":remoteCommandQueue,"delete":True}
    
    while True:
        
        rsp = card.Transaction(req)
        if "err" in rsp and str.__contains__(rsp["err"], "{note-noexist}"):
            break
        
        if "body" not in rsp:
            log.error("Expected body for event in Command queue")
            continue

        body = rsp["body"]

        with taskMutex:
            for c in body.items():
                command = c[0]
                arguments = c[1]
                if command in commandMap:
                    addTask(commandMap[command], arguments)
        



def armAttn(card):
    req = {"req":"card.attn", "mode":"arm,files","files":[testAttnResponseQueue, remoteCommandQueue]}
    card.Transaction(req)

    



def processAttnInfo(card):
    log.debug("ATTN Pin trigger sources")
    req = {"req":"card.attn"}
    
    rsp = card.Transaction(req)
    
    if "files" in rsp:
        files = rsp["files"]
        log.debug(f"Files: {files} ")
        if (remoteCommandQueue in files):
            enqueueCommands(card)

        if (testAttnResponseQueue in files):
            log.debug(f"there was a change to {testAttnResponseQueue}")

    
    log.debug("Rearm ATTN pin")
    card.Transaction({"req":"card.attn","mode":"rearm"})



def startTaskLoop():
    #Infinite loop that processes tasks in the task queue
    while True:
        with taskMutex:
            while len(taskList) > 0:
                t = taskList.pop(0)
                executeTask(t)


GPIO.setmode(GPIO.BCM)

# Configure RPi GPIO pin that is wired to the Notecard ATTN pin to detect rising edges
GPIO.setup(gpioAttnPin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)



def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

if __name__ == '__main__':

    
    productUID =     os.getenv("PRODUCT_UID", defaultProductUID)
    portType   =     os.getenv('PORT_TYPE',   defaultPortType).lower()
    portName   =     os.getenv('PORT_NAME',   defaultPortName)
    baudRate   = int(os.getenv('BAUD_RATE', str(defaultBaudRate)))
    host       =     os.getenv("HUB_HOST",    defaultHubHost)
    debugFlag  =     os.getenv("DEBUG",     str(defaultDebugFlag)).lower() in ('true', '1', 't')

    if debugFlag:
        log.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    

    log.info(f"Running: {__file__}")

    message = f"\nProduct: {productUID}\nHost: {host}\nDebug: {debugFlag}\nConnection Port Type:{portType}\nPort name: {portName}\n"
    log.info(message)

    log.debug(f"Connecting to Notecard using {portType} port type")
    if portType == 'i2c':
        port = I2C(portName)
        card = notecard.OpenI2C(port, 0, 0, debug=debugFlag)
    else:
        port = serial.Serial(port=portName,baudrate=baudRate)
        card = notecard.OpenSerial(port, debug=debugFlag)
        
    log.debug("Configuring Notecard Hub connection")
    configureNotecard(card, productUID=productUID, host=host)

    def attnIsrHandler(channel):
        processAttnInfo(card)

    GPIO.add_event_detect(gpioAttnPin, GPIO.RISING, callback=attnIsrHandler)
    
    armAttn(card)

    # Enables killing this script via Ctrl-C
    signal.signal(signal.SIGINT, signal_handler)
    
        
    startTaskLoop()




