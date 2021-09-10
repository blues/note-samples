import sqlite3

measurementTableName = "measurements"
alertTableName = "alerts"
class dbstore():
    _connection = None
    _cursor = None
    def __init__(self,file="") -> None:
        self._file = file


    def addMeasurement(self, deviceId, timestamp, type, value, units):

        d = (deviceId, timestamp, type, value, units,)

        self._cursor.execute(f'INSERT or REPLACE into {measurementTableName} VALUES(?,?,?,?,?)', d)
        self._connection.commit()

    def addAlert(self, deviceId, timestamp, type, message):

        d = (deviceId, timestamp, type, message,)

        self._cursor.execute(f'INSERT or REPLACE into {alertTableName} VALUES(?,?,?,?)', d)
        self._connection.commit()


    def connect(self) -> None:
        if self._connection is not None:
            return

        self._connection = sqlite3.connect(self._file)
        self._cursor = self._connection.cursor()

    def close(self) -> None:
        if not self._connection:
            return

        self._connection.close()
        self._connection = None

    def createTables(self):
        self._createMeasurementDataTableIfNotExist()
        self._createAlertTableIfNotExist()

    def getAlerts(self, limit=None):
        query = f""" SELECT * FROM {alertTableName}
                     ORDER BY ROWID DESC """

        if limit and limit > 0:
            query = f"""{query}
                      LIMIT {limit}
                     """
        c = self._cursor.execute(query)

        rows = c.fetchall()
        val = []
        for r in rows:
            val.append({
                "deviceId": r[0],
                "timestamp": r[1],
                "type": r[2],
                "message": r[3]
            })

        return val
        

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

        self._connection.commit()

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

    