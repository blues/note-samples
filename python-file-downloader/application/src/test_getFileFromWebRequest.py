#!/usr/bin/python3
# import json
# import os
# import sys
import time
#from periphery import I2C
import serial
import notecard
import base64
import zlib
import math



defaultProductUID = 'com.vsthose.admin:vstcp2'
defaultHost = "a.notefile.net"
print("Connecting to Notecard...")
# port = I2C("/dev/i2c-1")
# card = notecard.OpenI2C(port, 0, 0, debug=False)
port = serial.Serial(port="COM4",
                     baudrate=9600)
# port = serial.Serial(port="COM3",
#                      baudrate=115200)

nc = notecard.OpenSerial(port)



def current_milli_time():
  return math.floor(time.time() * 1000)

def configureNotecardForTestServer(card=nc):
  configureNotecard(card,productUID='gwolff.firmware.update',host="i.staging.blues.tools")

def configureNotecard(card = nc, productUID=defaultProductUID,host=defaultHost):
  print(f'Configuring Product: {productUID}...')

  req = {"req": "hub.set"}
  req["product"] = productUID
  #req["host"] = "i.staging.blues.tools"
  req["host"] = host
  req["mode"] = "continuous"
  req["outbound"] = 60
  req["inbound"] = 120
  req["sync"] = True
  req["align"] = True

  card.Transaction(req)



def get_sync_status(card = nc):
  req = {"req": "hub.sync.status"}
  rsp = card.Transaction(req)
  
  if "err" in rsp:
    return None

  if "status" in rsp:
    return rsp["status"]

  return "ready"

def get_connection_status(card=nc):
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

  syncInProgress =  syncStatus is not None and "{sync-end}" not in syncStatus and "ready" not in syncStatus and "web request" not in syncStatus
  if syncInProgress:
    return False
    

  return True




def web_get_chunk(file_to_update, chunk=1, card=nc):
  req = {"req": "web.get"}
  req["route"] = "remoteFileDownloader"
  req["name"] = f"?file={file_to_update}&chunk={chunk}"

  try:
    rsp = card.Transaction(req)
    print(rsp)
    if rsp["result"] != 200:
      return None


    return rsp
    
  except:
    # Using Serverless functions sometimes comes with a "warm-up" cost
    # that may cause the Notecard to timeout. Typically repeating the
    # request will solve this.
    return None

def chunk_is_valid(body):
  return zlib.crc32(body["payload"].encode('utf-8')) == body["crc32"]

get_file_from_remote_progress_timeout_ms = 30000
def get_file_from_remote(file_to_update):
  start_time = current_milli_time()
  expiration_time = start_time + get_file_from_remote_progress_timeout_ms

  next_chunk = 1
  last_chunk = 1
  file_string = ""
  print('Starting download...')
  while (next_chunk <= last_chunk):
    print("Downloading chunk: ", next_chunk)
    if (current_milli_time() > expiration_time):
      print("File download timeout")
      return None

    file_chunk = web_get_chunk(file_to_update, next_chunk)

    if file_chunk is None or "err" in file_chunk["body"]:
      continue
  
    body = file_chunk["body"]
    if not chunk_is_valid(body):
      continue

    last_chunk = int(body["total_chunks"])
    file_string += decode_content(body["payload"])

    next_chunk += 1
    expiration_time = current_milli_time() + get_file_from_remote_progress_timeout_ms

  return file_string


def decode_content(file_contents, asString=True):
  file_bytes = file_contents.encode('utf-8')
  contents_bytes = base64.b64decode(file_bytes)
  if asString:
    return contents_bytes.decode('utf-8')
  
  return contents_bytes

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


def main_loop():

  file_to_update = "downloader-example.png"
  
  file_update_attempt_expiration_ms = 0
  file_update_attempt_interval_ms = 5000
  while True:
    curr_time = current_milli_time()
    
    if (file_to_update is not None) & (curr_time > file_update_attempt_expiration_ms):
      success = attempt_file_download(file_to_update)
      if success:
        print("success!")
        file_to_update = None
        file_update_attempt_expiration_ms = 0
        #return  #<--- would not have this in main execution loop.  
      else:
        # update expiration for next file download attempt
        print("failed!")
        file_update_attempt_expiration_ms = curr_time + file_update_attempt_interval_ms
     

if __name__ == '__main__':
    fc = main_loop()
    #fc = get_file_from_remote("random-file.py")
    print(fc)

