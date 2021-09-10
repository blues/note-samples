from datetime import time
from flask_restful import Resource
import flask

def _defaultAddMeasurementFunc(device, timestamp, type,value, units):
    pass

class UploadMeasurementHandler(Resource):
    def __init__(self, addMeasurementFunc = _defaultAddMeasurementFunc) -> None:
        super().__init__()
        self._addMeasurement = addMeasurementFunc


    def post(self):
        json_input = flask.request.get_json()
        
        deviceId = json_input["device"]
        timestamp = json_input["when"]
        measurementType = json_input["body"]["type"]
        value = json_input["body"]["value"]
        units = json_input["body"]["units"]

        self._addMeasurement(deviceId, timestamp, measurementType, value, units)
        
        return {"message": "uploaded sensor data"}, 200

def _defaultAddAlertFunc(device, timestamp, type, message):
    pass

def _defaultGetAlertFunc(limit=None):
    pass

class UploadAlertHandler(Resource):
    def __init__(self, 
                 addAlertFunc = _defaultAddAlertFunc, 
                 getAlertFunc=_defaultGetAlertFunc) -> None:
        super().__init__()
        self._addAlert = addAlertFunc
        self._getAlert = getAlertFunc


    def post(self):
        json_input = flask.request.get_json()
        
        deviceId = json_input["device"]
        timestamp = json_input["when"]
        alertType = json_input["body"]["type"]
        message = json_input["body"]["message"]

        self._addAlert(deviceId, timestamp, alertType, message)

        return {"message": "uploaded alert"}, 200

    def get(self):
        val = self._getAlert(limit=50)

        return (val, 200,)