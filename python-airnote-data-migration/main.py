import notehub
import dbstore
import os

pin = os.getenv("NOTEHUB_PIN", None)
#dbFile = ":memory:"
dbFile = "airnote_data.db"

store = dbstore.dbstore(file=dbFile)

def migrateDataToDb(event):
    eventId = event.get("uid")
    deviceId = event.get("device_uid")
    timestamp = event.get("captured")
    location = event.get("gps_location")
    data=event.get("body")
    store.addMeasurement(deviceId, timestamp, data, location, eventId)

def migrateDeviceData(max_requests=10):

    devices = store.getDeviceList()
    for d in devices:
        lastEvent = store.getLastEventId(d)
        notehub.migrateAirnoteData(pin, d, migrateFunc=migrateDataToDb, since=lastEvent,max_requests=max_requests)


if __name__ == '__main__':

    # There must be at least one device listed to query any data from Notehub
    store.addDevice("dev:xxxxxxxxxxxxxx")
    # this call is not required if the database storing the list of devices is peristent
    # between executions of this script.

    migrateDeviceData()