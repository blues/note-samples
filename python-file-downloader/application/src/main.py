defaultProductUID = 'com.my.product.uid'
defaultHost = "a.notefile.net"
defaultFileDownloadDir = "./download"
defaultDebugFlag = False
defaultUseSerialFlag = False
defaultPortName = "/dev/i2c-1"
defaultBaudRate = 9600



import os
import sys
import shutil
    
try:
    from periphery import I2C #noqa:E402
except:
    pass

import serial

from timeit import default_timer as timer
import notecard
import dfu

appVersion = "1.7.0"
scriptName = __file__

def getUpdate(card, folder=defaultFileDownloadDir, statusWriter=lambda m:None):

    isAvailable = dfu.isUpdateAvailable(card)
    if not isAvailable:
        statusWriter("No update available")
        return None
    
    statusWriter("Update available for install")
        
    info = dfu.getUpdateInfo(card)
    
    isdir = os.path.isdir(folder)
    if not isdir:
        os.makedirs(folder)
    filename = os.path.join(folder, info["source"])

    message = "success"
    statusWriter("Copy update for installation")
    try:
        with open(filename, "wb") as f:
            p = lambda x:statusWriter(f"Migration {x}% complete")
            dfu.copyImageToWriter(card,f,progressUpdater=p)
    except Exception as e:
        statusWriter(f"Message: {e}")
        statusWriter("Failed to copy update")
        message = "failed to copy image to file"
        dfu.setUpdateError(card, message)
        return None

    else:
        statusWriter("Successfully copy of update")
        dfu.setUpdateDone(card, message)
    
    return filename
    


def getConnectionStatus(card):

    req = {"req":"hub.status"}
    rsp = card.Transaction(req)

    if "err" in rsp:
        return "UNKNOWN"

    return rsp["status"]

def displayConnectionStatus(card):
    s = getConnectionStatus(card)
    print(f"Connection status: {s}\n")

def restartApp(filename):
    shutil.copyfile(filename, scriptName)
    print(filename)
    print("Restarting program...")
    os.execv(sys.executable, [f'python {scriptName}'] + sys.argv[1:])


def start_check_update_loop(card):
    ten_second_timer = 0
    timer_interval_secs = 10
    while True:
        if timer() > ten_second_timer:
            try:
                displayConnectionStatus(card)
                filename = getUpdate(card,statusWriter=print)
                if filename:
                    restartApp(filename)
                
            except Exception as e:
                print(e)
            finally:
                ten_second_timer = timer() + timer_interval_secs






    

def configureNotecard(card, productUID=defaultProductUID,host=defaultHost):
  
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

    rsp = card.Transaction(req)

    if "err" in rsp:
        m = rsp["err"]
        raise Exception(f"Unable to configure Notecard connection: {m}")
    
    print(f"Configured Notecard connection:\n{rsp}")

    





def connectToNotecard(debugFlag = defaultDebugFlag,useSerial=defaultUseSerialFlag,portName=defaultPortName,baudRate=9600):
    if useSerial:
        port = serial.Serial(port=portName,baudrate=baudRate)
        card = notecard.OpenSerial(port, debug=debugFlag)
    else:
        port = I2C(portName)
        card = notecard.OpenI2C(port, 0, 0, debug=debugFlag)

    return card
    


if __name__ == '__main__':
    
    productUID = os.getenv("PRODUCT_UID", defaultProductUID)
    debugFlag  = os.getenv("DEBUG", str(defaultDebugFlag)).lower() in ('true', '1', 't')
    useSerial  = os.getenv('PORT_TYPE', str(defaultUseSerialFlag)).lower() in ('uart', 'usb','serial')
    portName   = os.getenv('PORT', defaultPortName)
    baud       = os.getenv('BAUD', str(defaultBaudRate))
    
    host       = os.getenv("HOST", defaultHost)
    scriptName = os.getenv('SCRIPT_NAME', scriptName)

    print(f"Running: {__file__}")

    message = f"\nProduct: {productUID}\nHost: {host}\nDebug: {debugFlag}\nUse Serial Connection:{useSerial}\nPort name: {portName}\nScript name: {scriptName}\n"
    print(message)

    nc = connectToNotecard(debugFlag=debugFlag,useSerial=useSerial,portName=portName,baudRate=int(baud))

    configureNotecard(nc, productUID=productUID, host=host)

    dfu.setVersion(nc, appVersion)

    start_check_update_loop(nc)
