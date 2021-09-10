import pytest
import dbstore

inMemFile = ":memory:"

measurementTable = "measurements"
alertTable = "alerts"

def test_db_store_constructor():
    s = dbstore.dbstore(file=inMemFile)

    assert(s != None)


timestampTestData = "2021-04-29T23:25:44Z"

def test_addMeasurement():
    s = dbstore.dbstore(file=inMemFile)

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
    s = dbstore.dbstore(file=inMemFile)

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

    
