#!/usr/bin/python3
import json
import os
import sys
from periphery import I2C
import notecard
import time
import math
import bme680
import base64
from gpiozero import InputDevice
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
port = I2C("/dev/i2c-1")
card = notecard.OpenI2C(port, 0, 0, debug=True)


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
    return "No status available"
  else:
    return rsp["status"]


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
    return web_get_chunk(file_to_update)


def get_file_from_remote(file_to_update):
  file_chunk = web_get_chunk(file_to_update)

  print(file_chunk)

  if "err" in file_chunk["body"]:
    return None
  else:
    body = file_chunk["body"]
    chunk_num = body["chunk_num"]
    total_chunks = body["total_chunks"]

    if total_chunks == 1:
      return body["payload"]
    else:
      print('File requires multiple requests...')
      file_string = body["payload"]

      for i in range(chunk_num+1, int(total_chunks)):
        print(f"Requesting chunk {i} of {total_chunks}")
        file_chunk = web_get_chunk(file_to_update, i)

        print(file_chunk)

        if "err" in file_chunk["body"]:
          return None
        else:
          file_string += file_chunk["body"]["payload"]

      return file_string


def save_file_and_restart(file_contents, file_name):
  file_bytes = file_contents.encode('utf-8')
  contents_bytes = base64.b64decode(file_bytes)
  decoded_file_contents = contents_bytes.decode('utf-8')

  with open(f"./src/{file_name}", "w") as text_file:
    print(decoded_file_contents, file=text_file)

  print("File updated. Restarting program...")
  os.execv(sys.executable, ['python'] + sys.argv)


main()
configure_attn()

attn_pin = 6
attn = InputDevice(attn_pin)

while True:
  curr_time = current_milli_time()
  file_to_update = None
  file_contents = None

  if attn.is_active:
    file_to_update = attn_fired()

  if file_to_update:
    print(f"Source file '{file_to_update}' has been updated remotely. Downloading...")

    # Make sure we aren't in the middle of a sync
    status = get_sync_status()
    while "{sync-end}" not in status and "{modem-off}" not in status:
      print("Waiting for sync to complete before continuing...")
      time.sleep(5)

    file_contents = get_file_from_remote(file_to_update)

    if file_contents:
      save_file_and_restart(file_contents, file_to_update)
      pass
    else:
      print('Unable to update file...')

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
