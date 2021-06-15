<<<<<<< HEAD
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
=======
#!/usr/bin/python3
import json
import os
import sys
import time
import math
#from periphery import I2C
import serial
import notecard
import bme680
import base64
from gpiozero import InputDevice
import zlib

import version

bme_sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)

bme_sensor.set_humidity_oversample(bme680.OS_2X)
bme_sensor.set_temperature_oversample(bme680.OS_8X)

bme_sensor.get_sensor_data()

productUID = 'com.blues.bsatrom:python_file_downloader'
SAMPLE_INTERVAL = 360 * 1000
last_reading_time = 0

notification_file = "file-update.qi"

print("*************")
print(f"Notecard File Downloader Sample version {version.get_version()}")
print("*************")
print("Connecting to Notecard...")
# port = I2C("/dev/i2c-1")
# card = notecard.OpenI2C(port, 0, 0, debug=False)
port = serial.Serial(port="COM4",
                     baudrate=9600)
# port = serial.Serial(port="COM3",
#                      baudrate=115200)

card = notecard.OpenSerial(port)


def main():
  print(f'Configuring Product: {productUID}...')

  req = {"req": "hub.set"}
  req["product"] = productUID
  req["mode"] = "continuous"
  req["outbound"] = 60
  req["inbound"] = 120
  req["sync"] = True
  req["align"] = True

  card.Transaction(req)


def current_milli_time():
  return math.floor(time.time() * 1000)


def configure_attn():
  print("Configuring ATTN...")

  req = {"req": "card.attn"}
  req["mode"] = "arm,files"
  req["files"] = [notification_file]
  req["seconds"] = 120

  card.Transaction(req)


def rearm_attn():
  print("Rearming ATTN...")

  req = {"req": "card.attn"}
  req["mode"] = "rearm"

  card.Transaction(req)


def get_updated_file_info():
  req = {"req": "note.get"}
  req["file"] = notification_file
  req["delete"] = True

  rsp = card.Transaction(req)

  if "err" in rsp:
    return None
  else:
    return rsp["body"]

def get_sync_status():
  req = {"req": "hub.sync.status"}
  rsp = card.Transaction(req)
  
  if "err" in rsp:
    return None

  if "status" in rsp:
    return rsp["status"]

  return "ready"

def get_connection_status():
  req = {"req":"hub.status"}
  rsp = card.Transaction(req)
  
  if "connected" in rsp:
    return rsp["connected"]
  
  return False

def notecard_is_ready_for_file_download():

  isConnected = get_connection_status()
  if not isConnected:
    return False
  
  syncStatus = get_sync_status()

  syncInProgress =  syncStatus & (syncStatus != "{sync-end}" & syncStatus != "ready")
  if syncInProgress:
    return False
    

  return True






def attn_fired():
  print("ATTN Fired, checking inbound message...")

  file_info = get_updated_file_info()

  rearm_attn()

  if file_info is not None:
    return file_info["name"]

  return None


def web_get_chunk(file_to_update, chunk=1):
  req = {"req": "web.get"}
  req["route"] = "remoteFileDownloader"
  req["name"] = f"?file={file_to_update}&chunk={chunk}"

  try:
    rsp = card.Transaction(req)

    return rsp
    
  except:
    # Using Serverless functions sometimes comes with a "warm-up" cost
    # that may cause the Notecard to timeout. Typically repeating the
    # request will solve this.
    return None

def chunk_is_valid(body):
  return zlib.crc32(body["payload"].encode('utf-8')) == body["crc32"]

get_file_from_remote_timeout_ms = 60000
def get_file_from_remote(file_to_update):
  start_time = current_milli_time()
  expiration_time = start_time + get_file_from_remote_timeout_ms

  next_chunk = 1
  last_chunk = 1
  file_string = ""
  print('Starting download...')
  while (next_chunk <= last_chunk):

    if (current_milli_time() < expiration_time):
      return None

    file_chunk = web_get_chunk(file_to_update, next_chunk)

    if not file_chunk | "err" in file_chunk["body"]:
      continue
  
    body = file_chunk["body"]
    if not chunk_is_valid(body):
      continue

    last_chunk = int(body["total_chunks"])
    file_string += body["payload"]

    next_chunk += 1

  return decode_file_content(file_string)


def decode_file_content(file_contents):
  file_bytes = file_contents.encode('utf-8')
  contents_bytes = base64.b64decode(file_bytes)
  return contents_bytes.decode('utf-8')

def save_file(file_contents, file_name):
  with open(f"./src/{file_name}", "w") as text_file:
    print(file_contents, file=text_file)

  print("File updated. Saved")
#  os.execv(sys.executable, ['python'] + sys.argv)


def attempt_file_download(file_to_update):
  if not notecard_is_ready_for_file_download():
    return False
  
  file_contents = None
  
  print(f"Source file '{file_to_update}' has been updated remotely. Downloading...")
  file_contents = get_file_from_remote(file_to_update)

  if file_contents:
    save_file(file_contents, file_to_update)
    return True
  
  print('Unable to update file...')
  return False


main()
configure_attn()

attn_pin = 6
attn = InputDevice(attn_pin)

file_to_update = None
file_update_attempt_expiration_ms = 0
file_update_attempt_interval_ms = 5000
while True:
  curr_time = current_milli_time()
  
  

  if attn.is_active:
    file_to_update = attn_fired()

  
  if file_to_update & (curr_time > file_update_attempt_expiration_ms):
    success = attempt_file_download(file_to_update)
    if success:
      file_to_update = None
      file_update_attempt_expiration_ms = 0
    else:
      # update expiration for next file download attempt
      file_update_attempt_expiration_ms = curr_time + file_update_attempt_interval_ms


    
      

  # check interval
  if (curr_time > last_reading_time + SAMPLE_INTERVAL):
    last_reading_time = curr_time
    bme_sensor.get_sensor_data()

    temp = bme_sensor.data.temperature
    humidity = bme_sensor.data.humidity

    print('Temperature: {} degrees C'.format(temp))
    print('Humidity: {}%'.format(humidity))

    req = {"req": "note.add"}
    req["file"] = "sensors.qo"
    req["sync"] = True
    req["body"] = { "temp": temp, "humidity": humidity}
    rsp = card.Transaction(req)
>>>>>>> Updates file download procedure
