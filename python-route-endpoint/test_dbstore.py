import pytest
import dbstore

inMemFile = ":memory:"

measurementTable = "measurements"
alertTable = "alerts"

def test_db_store_constructor():
    s = dbstore.dbstore(file=inMemFile)

    assert(s != None)


def test_dbStore_connect():
    s = dbstore.dbstore(file=inMemFile)
    s.connect()

    assert s._connection is not None

def test_dbStore_connect_whenConnectionIsOpen():
    s = dbstore.dbstore(file=inMemFile)
    s.connect()
    c = s._connection
    s.connect()
    assert s._connection == c



def test_dbStore_close_whenConnectionIsOpen():
    s = dbstore.dbstore(file=inMemFile)
    s.connect()
    assert s._connection is not None

    s.close()
    assert s._connection is None

def test_dbStore_close_whenConnectionIsClosed():
    s = dbstore.dbstore(file=inMemFile)
    assert s._connection is None
    s.close()
    assert s._connection is None


def test_dbStore_createTables():
    s = dbstore.dbstore(file="inMemFile")
    s.connect()
    s.createTables()
    for n in [measurementTable, alertTable]:
        s._cursor.execute(f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{n}';")
        isTable = s._cursor.fetchone()[0]==1
        assert isTable
        




timestampTestData = "2021-04-29T23:25:44Z"

def generateConnectedInMemDb() -> dbstore.dbstore:
    s = dbstore.dbstore(file=inMemFile)
    s.connect()
    s.createTables()
    return s

def test_addMeasurement():
    s = generateConnectedInMemDb()

    deviceId = "dev:xxxxxxxxxxxx"
    measurementType = "sensor1"
    timestamp = timestampTestData
    value = 3.14
    units = "units1"

    s.addMeasurement(deviceId, timestamp, measurementType, value, units)

    c = s._cursor.execute(f'SELECT * from {measurementTable}')
    row = c.fetchone()

    
    assert row[0]  == deviceId
    assert row[1]  == timestamp
    assert row[2]  == measurementType
    assert row[3]  == value
    assert row[4]  == units


def test_addAlert():
    s = generateConnectedInMemDb()

    deviceId = "dev:xxxxxxxxxxxx"
    alertType = "overfill"
    timestamp = timestampTestData
    message = "message 1"

    s.addAlert(deviceId, timestamp, alertType, message)

    c = s._cursor.execute(f'SELECT * from {alertTable}')
    row = c.fetchone()

    
    assert row[0]  == deviceId
    assert row[1]  == timestamp
    assert row[2]  == alertType
    assert row[3]  == message

    
def test_getAlerts():
    s = generateConnectedInMemDb()

    deviceId = "dev:xxxxxxxxxxxx"
    alertType = "overfill"
    timestamp = timestampTestData
    message = "message 1"

    s.addAlert(deviceId, timestamp, alertType, message)
    s.addAlert(deviceId, timestamp, alertType, message)

    a = s.getAlerts()
    
    e = [{"deviceId":deviceId,"timestamp":timestamp,"type":alertType,"message":message},
         {"deviceId":deviceId,"timestamp":timestamp,"type":alertType,"message":message},]
    
    assert a == e

def test_getAlerts_noAlertsStored():
    s = generateConnectedInMemDb()
    a = s.getAlerts()
    assert a == []

def test_getAlerts_withLimit():
    s = generateConnectedInMemDb()

    deviceId = "dev:xxxxxxxxxxxx"
    alertType = "overfill"
    timestamp = timestampTestData
    message = "message 1"

    s.addAlert(deviceId, timestamp, alertType, message)
    s.addAlert(deviceId, timestamp, alertType, message)

    a = s.getAlerts(limit=1)
    
    e = [{"deviceId":deviceId,"timestamp":timestamp,"type":alertType,"message":message}]
    
    assert a == e