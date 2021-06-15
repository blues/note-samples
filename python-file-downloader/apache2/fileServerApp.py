

from flask import Flask
from flask_restful import Api
from server.handler import DownloadHandler
from server.reader import FileReader
import os

app = Flask(__name__)
api = Api(app)

rootPath  = os.path.dirname(__file__)
assetPath = os.path.join(rootPath, '../assets')
f = FileReader(asset_path=assetPath)

api.add_resource(DownloadHandler, '/download', endpoint='download',resource_class_args=(f,))
print(f.asset_path)

if __name__ == '__main__':
    #api.add_resource(HelloWorld,'/blah', endpoint='blah')
    app.run(host='0.0.0.0', port=8443)
