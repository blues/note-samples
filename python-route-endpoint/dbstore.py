import sqlite3

measurementTableName = "measurements"
alertTableName = "alerts"
class dbstore():
    def __init__(self,file="") -> None:
        self._connectToDb(file)
        self._createMeasurementDataTableIfNotExist()
        self._createAlertTableIfNotExist()


    def addMeasurement(self, deviceId, timestamp, type, value, units):

        d = (deviceId, timestamp, type, value, units,)

        self._cursor.execute(f'INSERT or REPLACE into {measurementTableName} VALUES(?,?,?,?,?)', d)
        self._connection.commit()

    def addAlert(self, deviceId, timestamp, type, message):

        d = (deviceId, timestamp, type, message,)

        self._cursor.execute(f'INSERT or REPLACE into {alertTableName} VALUES(?,?,?,?)', d)
        self._connection.commit()


    def _connectToDb(self,file) -> None:
        self._connection = sqlite3.connect(file)
        self._cursor = self._connection.cursor()


    def _createMeasurementDataTableIfNotExist(self):
        self._cursor.execute(f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{measurementTableName}';")
        isTable = self._cursor.fetchone()[0]==1

        if isTable:
            return
        
        self._cursor.execute(f"""CREATE TABLE 
          {measurementTableName}(
              device_id STRING, 
              timestamp STRING, 
              type STRING,
              value FLOAT,
              units STRING
           );""")

    def _createAlertTableIfNotExist(self):
        self._cursor.execute(f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{alertTableName}';")
        isTable = self._cursor.fetchone()[0]==1

        if isTable:
            return
        
        self._cursor.execute(f"""CREATE TABLE 
          {alertTableName}(
              device_id STRING, 
              timestamp STRING, 
              type STRING,
              message STRING
           );""")

    