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


#productUID = 'gwolff.firmware.update'
productUID = 'com.vsthose.admin:vstcp2'
print("Connecting to Notecard...")
# port = I2C("/dev/i2c-1")
# card = notecard.OpenI2C(port, 0, 0, debug=False)
port = serial.Serial(port="COM4",
                     baudrate=9600)
# port = serial.Serial(port="COM3",
#                      baudrate=115200)

nc = notecard.OpenSerial(port)


def configureNotecard(card = nc):
  print(f'Configuring Product: {productUID}...')

  req = {"req": "hub.set"}
  req["product"] = productUID
  #req["host"] = "i.staging.blues.tools"
  req["host"] = "a.notefile.net"
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
    return "No status available"
  else:
    return rsp["status"]



def web_get_chunk(card = nc, file_to_update="", chunk=1):
  req = {"req": "web.get"}
  req["route"] = "remoteFileDownloader"
  req["name"] = f"?file={file_to_update}&chunk={chunk}"

  try:
    rsp = card.Transaction(req)

    if "err" in rsp["body"]:
      return None

    # Perform a crc32 on the chunk to make sure it matches what we should get.
    # If not, request again.
    body = rsp["body"]
    if zlib.crc32(body["payload"].encode('utf-8')) == body["crc32"]:
      return rsp
    else:
      print("Communication error downloading chunk. Retrying...")
      return web_get_chunk(card, file_to_update)
  except:
    # Using Sert.verless functions sometimes comes with a "warm-up" cost
    # that may cause the Notecard to timeout. Typically repeating the
    # request will solve this.
    return web_get_chunk(card, file_to_update)


def get_file_from_remote(card=nc,file_to_update=""):
  print('Requesting first chunk...')
  file_chunk = web_get_chunk(file_to_update)

  if "err" in file_chunk["body"]:
    return None
  else:
    body = file_chunk["body"]
    chunk_num = body["chunk_num"]
    total_chunks = int(body["total_chunks"])

    if total_chunks == 1:
      return body["payload"]
    else:
      print('File requires multiple requests...')
      file_string = body["payload"]

      for i in range(chunk_num+1, total_chunks):
        print(f"Requesting chunk {i} of {total_chunks}")
        file_chunk = web_get_chunk(file_to_update, i)

        if "err" in file_chunk["body"]:
          return None
        else:
          file_string += file_chunk["body"]["payload"]

      return file_string


def decode_file_contents(file_contents):
  file_bytes = file_contents.encode('utf-8')
  contents_bytes = base64.b64decode(file_bytes)
  decoded_file_contents = contents_bytes.decode('utf-8')

  return decoded_file_contents




def doFileUpdate(file_to_update):


    # Make sure we aren't in the middle of a sync
    status = get_sync_status()
    while "{sync-end}" not in status and "{modem-off}" not in status:
      print("Waiting for sync to complete before continuing...")
      time.sleep(5)
      status = get_sync_status()

    file_contents = get_file_from_remote(file_to_update)

    if not file_contents:
        print('Unable to update file...')
      
        pass
    
    content = decode_file_contents(file_contents)

    print(content)
     

if __name__ == '__main__':
    rsp = web_get_chunk(nc, "test.py", 1)
    numChunks = rsp["body"]["total_chunks"]
    chunk = 2
    while "err" not in rsp["body"]:
        rsp = web_get_chunk(nc, "test.py", chunk)
        print(rsp)
        chunk = chunk + 1
        if chunk > numChunks:
            chunk = 1

