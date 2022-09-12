from datetime import datetime
import sqlite3

class dbstore():
    def __init__(self,file="") -> None:
        self._connectToDb(file)
        self._createDeviceTableIfNotExist()
        self._createAirDataTableIfNotExist()

    def addDevice(self, id):
        c = self._cursor.execute('INSERT or IGNORE into devices(device_id) VALUES(?)',(id,))
        self._connection.commit()

    def removeDevice(self, id):
        self._cursor.execute("DELETE FROM devices WHERE device_id = ?",(id,))
        self._connection.commit()

    def getDeviceList(self):

        c = self._cursor
        rf = c.row_factory
        c.row_factory = lambda cursor, row: row[0]
        c.execute('SELECT device_id from devices')
        devices = c.fetchall()
        c.row_factory = rf
        return devices


    def addMeasurement(self, deviceId, timestamp, data, latitude, longitude, eventId):

        ts = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')
        
        d = (eventId, 
             deviceId, 
             ts, 
             latitude,
             longitude,
             data.get('c00_30'),
             data.get('c00_50'),
             data.get('c01_00'),
             data.get('c02_50'),
             data.get('charging'),
             data.get('csamples'),
             data.get('csecs'),
             data.get('humidity'),
             data.get('pm01_0'),
             data.get('pm01_0_rstd'),
             data.get('pm02_5'),
             data.get('pm02_5_rstd'),
             data.get('pm10_0'),
             data.get('pm10_0_rstd'),
             data.get('pressure'),
             data.get('temperature'),
             data.get('voltage'),
             data.get('sensor'),
        )

        self._cursor.execute('INSERT or REPLACE into airdata VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', d)
        self._connection.commit()


    def getLastEventId(self, deviceId):
        c = self._cursor.execute(""" SELECT event_id FROM airdata
                                 WHERE device_id=?
                                 ORDER BY ROWID DESC
                                 LIMIT 1
        """, (deviceId,))

        val = c.fetchone()
        if val == None:
            return None

        return val[0]


    def exportToCsv(self,filename,deviceId=None):
        import csv
        cursor = self._cursor
        query = "SELECT * FROM airdata"
        if deviceId:
            query = f"{query} WHERE device_id=\"{deviceId}\"" 

        c = cursor.execute(query)
        with open(filename, "w") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([i[0] for i in c.description])
            csv_writer.writerows(c)

    def _connectToDb(self,file) -> None:
        self._connection = sqlite3.connect(file)
        self._cursor = self._connection.cursor()

    def _createDeviceTableIfNotExist(self):
        self._cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='devices';")
        isTable = self._cursor.fetchone()[0]==1

        if isTable:
            return
        
        self._cursor.execute("CREATE TABLE devices(device_id STRING,UNIQUE(device_id));")

    def _createAirDataTableIfNotExist(self):
        self._cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='airdata';")
        isTable = self._cursor.fetchone()[0]==1

        if isTable:
            return
        
        self._cursor.execute("""CREATE TABLE 
          airdata(
              event_id STRING, 
              device_id STRING, 
              timestamp STRING, 
              latitude FLOAT, 
              longitude FLOAT,
              c00_30 INT,
              c00_50 INT,
              c01_00 INT,
              c02_50 INT,
              charging BOOL,
              csamples INT,
              csecs INT,
              humidity FLOAT,
              pm01_0  FLOAT,
              pm01_0_rstd  FLOAT,
              pm02_5  FLOAT,
              pm02_5_rstd  FLOAT,
              pm10_0  FLOAT,
              pm10_0_rstd  FLOAT,
              pressure FLOAT,
              temperature FLOAT,
              voltage FLOAT,
              sensor STRING,
        UNIQUE(event_id));""")





