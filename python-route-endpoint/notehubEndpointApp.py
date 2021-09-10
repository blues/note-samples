
from flask import Flask, g
from flask_restful import Api
from werkzeug.datastructures import UpdateDictMixin

from dbstore import dbstore
from handler import UploadAlertHandler, UploadMeasurementHandler

app = Flask(__name__)
api = Api(app)


store = dbstore(file="data.db")

api.add_resource(UploadMeasurementHandler, '/measurements',endpoint='measurements',resource_class_args=(store.addMeasurement,) )
api.add_resource(UploadAlertHandler, '/alerts',endpoint='alerts',resource_class_args=(store.addAlert,) )

@app.before_request
def before_request():
    g.store = store
    g.store.connect()


@app.after_request
def after_request(response):
    g.store.close()
    return response

if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=8443)
    app.run(host='0.0.0.0', port=5000)