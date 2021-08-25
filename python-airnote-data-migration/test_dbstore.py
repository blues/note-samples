import pytest
import dbstore

inMemFile = ":memory:"

def test_db_store_constructor():
    s = dbstore.dbstore(file=inMemFile)

    assert(s != None)

def test_addDevice():
    s = dbstore.dbstore(file=inMemFile)
    deviceId = "dev:xxxxxxxxxxxx"
    s.addDevice(deviceId)

    c = s._cursor.execute('SELECT * from devices')
    deviceInTable = c.fetchone()[0]
    
    assert deviceId == deviceInTable

def test_addDevice_anotherNewDevice():
    s = dbstore.dbstore(file=inMemFile)
    deviceId1 = "dev:xxxxxxxxxxxx"
    deviceId2 = "dev:yyyyyyyyyyyy"
    s.addDevice(deviceId1)
    s.addDevice(deviceId2)

    c = s._cursor.execute('SELECT * from devices')
    deviceInTable2 = c.fetchall()[1][0]
    
    assert deviceId2 == deviceInTable2

def test_addDevice_sameDeviceMultipleTimes():
    s = dbstore.dbstore(file=inMemFile)
    deviceId = "dev:xxxxxxxxxxxx"
    s.addDevice(deviceId)
    s.addDevice(deviceId)

    c = s._cursor.execute('SELECT COUNT(*) from devices')
    numEntries = c.fetchone()[0]
    
    assert numEntries == 1


def test_getDeviceList():
    s = dbstore.dbstore(file=inMemFile)
    deviceId1 = "dev:xxxxxxxxxxxx"
    deviceId2 = "dev:yyyyyyyyyyyy"
    s.addDevice(deviceId1)
    s.addDevice(deviceId2)

    d = s.getDeviceList()
    
    assert d == [deviceId1, deviceId2]

def test_getDeviceList_noDevices_emptyList():
    s = dbstore.dbstore(file=inMemFile)
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

timestampTestData = "2021-04-29T23:25:44Z"

def test_addMeasurement():
    s = dbstore.dbstore(file=inMemFile)

    deviceId = "dev:xxxxxxxxxxxx"
    location = locationTestData
    timestamp = timestampTestData
    eventUid = "ee0f7c1b-754c-4a4b-84fe-07cf3d96ec53"

    data = measurementTestData

    s.addMeasurement(deviceId, timestamp, data, location, eventUid)

    c = s._cursor.execute('SELECT * from airdata')
    row = c.fetchone()

    assert row[0]  == eventUid
    assert row[1]  == deviceId
    assert row[2]  == timestamp
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
    s = dbstore.dbstore(file=inMemFile)

    deviceId = "dev:xxxxxxxxxxxx"
    location = locationTestData
    timestamp = timestampTestData
    eventUid = "ee0f7c1b-754c-4a4b-84fe-07cf3d96ec53"

    data = {"temperature":13.0}

    s.addMeasurement(deviceId, timestamp, data, location, eventUid)

    c = s._cursor.execute('SELECT * from airdata')
    row = c.fetchone()

    temperature = row[20]
    assert temperature == 13.0

    data = {"temperature":17.0}
    s.addMeasurement(deviceId, timestamp, data, location, eventUid)

    c = s._cursor.execute('SELECT COUNT(*) from airdata')
    numEntries = c.fetchone()[0]
    assert numEntries == 1

    c = s._cursor.execute('SELECT * from airdata')
    row = c.fetchone()

    temperature = row[20]
    assert temperature == 17.0


def test_getLastEventId():
    s = dbstore.dbstore(file=inMemFile)
    deviceId = "dev:xxxxxxxxxxxx"
    eventUid = "fegh"
    s.addMeasurement(deviceId, None, {}, {}, 'abcdefg')
    s.addMeasurement(deviceId, None, {}, {}, eventUid)
    s.addMeasurement('dev:yyyyyyyyyyyyy', None, {}, {}, 'qrtstuv')

    lastUid = s.getLastEventId(deviceId)

    assert lastUid == eventUid



def test_getLastEventId_noDevice():
    s = dbstore.dbstore(file=inMemFile)
    deviceId = "dev:xxxxxxxxxxxx"
    eventUid = "fegh"
    s.addMeasurement(deviceId, None, {}, {}, eventUid)

    lastUid = s.getLastEventId(deviceId+'y')

    assert lastUid == None



def test_addMeasurement_noLocation():
    s = dbstore.dbstore(file=inMemFile)

    deviceId = "dev:xxxxxxxxxxxx"
    location = {}
    timestamp = timestampTestData
    eventUid = "ee0f7c1b-754c-4a4b-84fe-07cf3d96ec53"

    data = measurementTestData

    s.addMeasurement(deviceId, timestamp, data, location, eventUid)
    c = s._cursor.execute('SELECT latitude,longitude from airdata')
    row = c.fetchone()

    assert row == (None,None)

def test_addMeasurement_LocationIsNone():
    s = dbstore.dbstore(file=inMemFile)

    deviceId = "dev:xxxxxxxxxxxx"
    location = None
    timestamp = timestampTestData
    eventUid = "ee0f7c1b-754c-4a4b-84fe-07cf3d96ec53"

    data = measurementTestData

    s.addMeasurement(deviceId, timestamp, data, location, eventUid)
    c = s._cursor.execute('SELECT latitude,longitude from airdata')
    row = c.fetchone()

    assert row == (None,None)



    