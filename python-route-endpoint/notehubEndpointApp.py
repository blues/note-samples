
from flask import Flask
from flask_restful import Api

from dbstore import dbstore
from handler import UploadMeasurementHandler

app = Flask(__name__)
api = Api(app)


store = dbstore(file="data.db")

api.add_resource(UploadMeasurementHandler, '/measurements',endpoint='measurements',resource_class_args=(store.addMeasurement,) )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8443)