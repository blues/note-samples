import notehub
import dbstore
import os

pin = os.getenv("NOTEHUB_PIN", None)
#dbFile = ":memory:"
dbFile = "airnote_data.db"

store = dbstore.dbstore(file=dbFile)

def migrateDataToDb(event):
    eventId = event.get("event")
    deviceId = event.get("device")
    timestamp = event.get("when")
    latitude = event.get("where_lat")
    longitude = event.get("where_lon")
    data=event.get("body")
    store.addMeasurement(deviceId, timestamp, data, latitude, longitude, eventId)

def migrateDeviceData(max_requests=10):

    devices = store.getDeviceList()
    for d in devices:
        lastEvent = store.getLastEventId(d)
        notehub.migrateAirnoteData(pin, d, migrateFunc=migrateDataToDb, cursor=lastEvent,max_requests=max_requests)


def getCommandLineArgs():

    DESCRIPTION = """Migrate Airnote data from Notehub cloud storage to local database.
    MUST add at least 1 Airnote device ID for migration to occur.
    
    With no arguments, performs migration by default"""

    import argparse
    parser = argparse.ArgumentParser(description=DESCRIPTION, 
                                 formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-x","--export", help="export data to CSV to a specific file", default="", metavar="FILENAME")
    parser.add_argument("-d","--device", help="filter CSV export to a specific by supplying the device ID", default=None, metavar="DEVICE_UID")
    group.add_argument('-a', "--add-device", nargs='+', help="Add Airnote(s) to list of Airnotes to gather data supplying at least 1 device ID", dest='add_device', metavar="DEVICE_UID")
    group.add_argument('-r', "--remove-device", nargs='+', help="Remove Airnote(s) from list of Airnotes by supplying at least 1 device ID",dest='remove_device', metavar="DEVICE_UID")
    group.add_argument('-l', '--list-devices', help='echo list of Airnote device IDs whose data is migrated to local database', action="store_true", dest="list_devices")
    group.add_argument('-m', '--migrate', help="(DEFAULT ACTION) Download data from Notehub cloud service and store in local database", action="store_true", default=True)
    
    
    args = parser.parse_args()

    return args

if __name__ == '__main__':
    
    import sys

    args = getCommandLineArgs()

    if args.export:
        f = args.export
        deviceId = args.device if args.device else None
        print(f"exporting data for {deviceId} to {f}")
        store.exportToCsv(f, deviceId=deviceId)
        sys.exit(0)

    # There must be at least one device added to enable download any data from Notehub
    if args.add_device:
        for d in args.add_device:
            print(f"Adding device: {d}")
            store.addDevice(d)

        sys.exit(0)

    if args.remove_device:
        for d in args.remove_device:
            print(f"Removing device: {d}")
            store.removeDevice(d)

        sys.exit(0)

    if args.list_devices:
        print("Airnotes where migration is active")
        devices = store.getDeviceList()
        print(devices)
        sys.exit(0)

    print("Migrating device data from Notehub to local storage")
    migrateDeviceData()

    