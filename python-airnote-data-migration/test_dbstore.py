
import dbstore

useMem = True

if not useMem:
    import uuid

def getDbFile():
    if useMem:
        return ":memory:"

    fn = str(uuid.uuid4()) + ".db"
    return fn


import contextlib
import os

@contextlib.contextmanager
def temporary_filename(suffix=None):
  """Context that introduces a temporary file.

  Creates a temporary file, yields its name, and upon context exit, deletes it.
  (In contrast, tempfile.NamedTemporaryFile() provides a 'file' object and
  deletes the file as soon as that file object is closed, so the temporary file
  cannot be safely re-opened by another library or process.)

  Args:
    suffix: desired filename extension (e.g. '.mp4').

  Yields:
    The name of the temporary file.
  """
  import tempfile
  try:
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_name = f.name
    f.close()
    yield tmp_name
  finally:
    os.unlink(tmp_name)

def test_db_store_constructor():
    s = dbstore.dbstore(file=getDbFile())

    assert(s != None)

def test_addDevice():
    s = dbstore.dbstore(file=getDbFile())
    deviceId = "dev:xxxxxxxxxxxx"
    s.addDevice(deviceId)

    c = s._cursor.execute('SELECT * from devices')
    deviceInTable = c.fetchone()[0]
    
    assert deviceId == deviceInTable

def test_addDevice_anotherNewDevice():
    s = dbstore.dbstore(file=getDbFile())
    deviceId1 = "dev:xxxxxxxxxxxx"
    deviceId2 = "dev:yyyyyyyyyyyy"
    s.addDevice(deviceId1)
    s.addDevice(deviceId2)

    c = s._cursor.execute('SELECT * from devices')
    deviceInTable2 = c.fetchall()[1][0]
    
    assert deviceId2 == deviceInTable2

def test_addDevice_sameDeviceMultipleTimes():
    s = dbstore.dbstore(file=getDbFile())
    deviceId = "dev:xxxxxxxxxxxx"
    s.addDevice(deviceId)
    s.addDevice(deviceId)

    c = s._cursor.execute('SELECT COUNT(*) from devices')
    numEntries = c.fetchone()[0]
    
    assert numEntries == 1


def test_removeDevice_noDevicesInTable():
    s = dbstore.dbstore(file=getDbFile())
    deviceId = "dev:xxxxxxxxxxxx"
    s.removeDevice(deviceId)

def test_removeDevice_oneDeviceInTable():
    s = dbstore.dbstore(file=getDbFile())
    deviceId = "dev:xxxxxxxxxxxx"
    s.addDevice(deviceId)

    s.removeDevice(deviceId)

    c = s._cursor.execute('SELECT COUNT(*) from devices')
    numEntries = c.fetchone()[0]
    
    assert numEntries == 0

def test_removeDevice_multipleDevicesInTable():
    s = dbstore.dbstore(file=getDbFile())
    deviceId = "dev:xxxxxxxxxxxx"
    s.addDevice(deviceId)
    s.addDevice("abcdef")

    s.removeDevice(deviceId)

    c = s._cursor.execute('SELECT COUNT(*) from devices')
    numEntries = c.fetchone()[0]
    
    assert numEntries == 1

def test_removeDevice_deviceIdNotInTable():
    s = dbstore.dbstore(file=getDbFile())
    deviceId = "dev:xxxxxxxxxxxx"
    s.addDevice("abcdef")

    s.removeDevice(deviceId)

    c = s._cursor.execute('SELECT COUNT(*) from devices')
    numEntries = c.fetchone()[0]
    
    assert numEntries == 1


def test_getDeviceList():
    s = dbstore.dbstore(file=getDbFile())
    deviceId1 = "dev:xxxxxxxxxxxx"
    deviceId2 = "dev:yyyyyyyyyyyy"
    s.addDevice(deviceId1)
    s.addDevice(deviceId2)

    d = s.getDeviceList()
    
    assert d == [deviceId1, deviceId2]

def test_getDeviceList_noDevices_emptyList():
    s = dbstore.dbstore(file=getDbFile())
    d = s.getDeviceList()

    assert d == []



measurementTestData = {
        "c00_30": 1370,
        "c00_50": 393,
        "c01_00": 57,
        "c02_50": 2,
        "charging": True,
        "csamples": 29,
        "csecs": 60,
        "humidity": 49.80455,
        "pm01_0": 5.862069,
        "pm01_0_rstd": 0.16894531,
        "pm02_5": 8.4827585,
        "pm02_5_rstd": 0.15637207,
        "pm10_0": 9.068966,
        "pm10_0_rstd": 0.10180664,
        "pressure": 102278.41,
        "sensor": "pms7003",
        "temperature": 29.07207,
        "voltage": 3.5039062
    }

locationTestData = {"latitude": 42.381712500000006,
        "longitude": -72.536109375}

timestampTestData = 1577841940
tsTestData = '2020-01-01 01:25:40.000000'

def test_addMeasurement():
    s = dbstore.dbstore(file=getDbFile())

    deviceId = "dev:xxxxxxxxxxxx"
    location = locationTestData
    timestamp = timestampTestData
    eventUid = "ee0f7c1b-754c-4a4b-84fe-07cf3d96ec53"

    data = measurementTestData

    s.addMeasurement(deviceId, timestamp, data, location["latitude"], location["longitude"], eventUid)

    c = s._cursor.execute('SELECT * from airdata')
    row = c.fetchone()

    assert row[0]  == eventUid
    assert row[1]  == deviceId
    assert row[2]  == tsTestData
    assert row[3]  == location["latitude"]
    assert row[4]  == location["longitude"]
    assert row[5]  == data["c00_30"]
    assert row[6]  == data["c00_50"]
    assert row[7]  == data["c01_00"]
    assert row[8]  == data["c02_50"]
    assert row[9]  == data["charging"]
    assert row[10] == data["csamples"]
    assert row[11] == data["csecs"]
    assert row[12] == data["humidity"]
    assert row[13] == data["pm01_0"]
    assert row[14] == data["pm01_0_rstd"]
    assert row[15] == data["pm02_5"]
    assert row[16] == data["pm02_5_rstd"]
    assert row[17] == data["pm10_0"]
    assert row[18] == data["pm10_0_rstd"]
    assert row[19] == data["pressure"]
    assert row[20] == data["temperature"]
    assert row[21] == data["voltage"]
    assert row[22] == data["sensor"]


    

def test_addMeasurement_sameEventMultipleTimes():
    s = dbstore.dbstore(file=getDbFile())

    deviceId = "dev:xxxxxxxxxxxx"
    location = locationTestData
    timestamp = timestampTestData
    eventUid = "ee0f7c1b-754c-4a4b-84fe-07cf3d96ec53"

    data = {"temperature":13.0}

    s.addMeasurement(deviceId, timestamp, data, location["latitude"], location["longitude"], eventUid)

    c = s._cursor.execute('SELECT * from airdata')
    row = c.fetchone()

    temperature = row[20]
    assert temperature == 13.0

    data = {"temperature":17.0}
    deviceId = "dev:yyyyyyyyyyyyy"
    s.addMeasurement(deviceId, timestamp, data, location["latitude"], location["longitude"], eventUid)

    c = s._cursor.execute('SELECT COUNT(*) from airdata')
    numEntries = c.fetchone()[0]
    assert numEntries == 1

    c = s._cursor.execute('SELECT * from airdata')
    row = c.fetchone()

    temperature = row[20]
    assert temperature == 17.0


def test_getLastEventId():
    s = dbstore.dbstore(file=getDbFile())
    deviceId = "dev:xxxxxxxxxxxx"
    eventUid = "fegh"
    s.addMeasurement(deviceId, timestampTestData, {}, None, None, 'abcdefg')
    s.addMeasurement(deviceId, timestampTestData, {}, None, None, eventUid)
    s.addMeasurement('dev:yyyyyyyyyyyyy', timestampTestData, {}, None, None, 'qrtstuv')

    lastUid = s.getLastEventId(deviceId)

    assert lastUid == eventUid



def test_getLastEventId_noDevice():
    s = dbstore.dbstore(file=getDbFile())
    deviceId = "dev:xxxxxxxxxxxx"
    eventUid = "fegh"
    s.addMeasurement(deviceId, timestampTestData, {}, None, None, eventUid)

    lastUid = s.getLastEventId(deviceId+'y')

    assert lastUid == None



def test_addMeasurement_noLocation():
    s = dbstore.dbstore(file=getDbFile())

    deviceId = "dev:xxxxxxxxxxxx"
    timestamp = timestampTestData
    eventUid = "ee0f7c1b-754c-4a4b-84fe-07cf3d96ec53"

    data = measurementTestData

    s.addMeasurement(deviceId, timestamp, data, None, None, eventUid)
    c = s._cursor.execute('SELECT latitude,longitude from airdata')
    row = c.fetchone()

    assert row == (None,None)

def test_addMeasurement_LocationIsNone():
    s = dbstore.dbstore(file=getDbFile())

    deviceId = "dev:xxxxxxxxxxxx"
    timestamp = timestampTestData
    eventUid = "ee0f7c1b-754c-4a4b-84fe-07cf3d96ec53"

    data = measurementTestData

    s.addMeasurement(deviceId, timestamp, data, None, None, eventUid)
    c = s._cursor.execute('SELECT latitude,longitude from airdata')
    row = c.fetchone()

    assert row == (None,None)



def test_exportToCsv():
    import csv
    s = dbstore.dbstore(file=getDbFile())
    

    deviceId = "dev:xxxxxxxxxxxx"
    location = locationTestData
    timestamp = timestampTestData
    eventUid = "ee0f7c1b-754c-4a4b-84fe-07cf3d96ec53"

    data = measurementTestData

    s.addMeasurement(deviceId, timestamp, data, location["latitude"], location["longitude"], eventUid)
    with temporary_filename() as f:
        s.exportToCsv(f,deviceId=deviceId)
        
        assert os.path.exists(f)

        with open(f, 'r') as data:
      
            for line in csv.DictReader(data):
                print(line)
        
    assert line["event_id"] == eventUid
    assert line["device_id"] == deviceId
    assert float(line["latitude"]) == locationTestData["latitude"]
    assert float(line["longitude"]) == locationTestData["longitude"]
    assert int(line["c00_30"]) == measurementTestData["c00_30"]
    assert int(line["c00_50"]) == measurementTestData["c00_50"]
    assert int(line["c01_00"]) == measurementTestData["c01_00"]
    assert int(line["c02_50"]) == measurementTestData["c02_50"]
    assert bool(line["charging"]) == measurementTestData["charging"]
    assert int(line["csamples"]) == measurementTestData["csamples"]
    assert int(line["csecs"]) == measurementTestData["csecs"]
    assert float(line["humidity"]) == measurementTestData["humidity"]
    assert float(line["pm01_0"]) == measurementTestData["pm01_0"]
    assert float(line["pm01_0_rstd"]) == measurementTestData["pm01_0_rstd"]
    assert float(line["pm02_5"]) == measurementTestData["pm02_5"]
    assert float(line["pm02_5_rstd"]) == measurementTestData["pm02_5_rstd"]
    assert float(line["pm10_0"]) == measurementTestData["pm10_0"]
    assert float(line["pm10_0_rstd"]) == measurementTestData["pm10_0_rstd"]
    assert float(line["pressure"]) == measurementTestData["pressure"]
    assert float(line["temperature"]) == measurementTestData["temperature"]
    assert float(line["voltage"]) == measurementTestData["voltage"]
    assert line["sensor"] == measurementTestData["sensor"]


def test_exportToCsv_noDeviceId():
    import csv
    s = dbstore.dbstore(file=getDbFile())
    

    deviceId1 = "dev:xxxxxxxxxxxx"
    deviceId2 = "dev:yyyyyyyyyyyy"
    
    location = locationTestData
    timestamp = timestampTestData
    eventUid1 = "ee0f7c1b-754c-4a4b-84fe-07cf3d96ec53"
    eventUid2 = "ee0f7c1b-754c-4a4b-84fe-07cf3d96ec54"

    data = measurementTestData
    
    s.addMeasurement(deviceId1, timestamp, data, location["latitude"], location["longitude"], eventUid1)
    s.addMeasurement(deviceId2, timestamp, data, location["latitude"], location["longitude"], eventUid2)
    with temporary_filename() as f:
        s.exportToCsv(f,deviceId=None)
        
        assert os.path.exists(f)

        with open(f, 'r') as data:
            
            deviceIds =[]
            r = csv.DictReader(data)
            for line in r:
                deviceIds.append(line["device_id"])
            
        
    assert len(deviceIds) == 2
    assert deviceIds[0] == deviceId1
    assert deviceIds[1] == deviceId2
    