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