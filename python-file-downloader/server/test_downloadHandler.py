import unittest
from unittest.mock import Mock


from server import handler
from server.reader import FileReader
from flask import Flask
import base64

def raiseFileException(arg):
    raise Exception('foo')

class TestDownloadHandler(unittest.TestCase):

    def test_constructor_fileReader(self):
        reader = Mock(spec=FileReader)
        h = handler.DownloadHandler(fileReader=reader)
        self.assertEqual(h._fileReader, reader)


    def test_get_fileNotAvailable_400WithMessage(self):
        app = Flask(__name__)
        expectedResponse = ({'message': 'internal server error'}, 400)
        reader = Mock(spec=FileReader)
        reader.read.side_effect = raiseFileException

        h = handler.DownloadHandler(fileReader=reader)
        with app.test_request_context('/?file="abc"',method='GET'):
            r = h.dispatch_request()
            self.assertTupleEqual(r, expectedResponse)

    def test_get_fileAvailable(self):
        data = b'hello world'
        expectedData = base64.b64encode(data).decode("UTF-8")
        app = Flask(__name__)
        reader = Mock(spec=FileReader)
        reader.read.return_value = data

        h = handler.DownloadHandler(fileReader = reader)
        with app.test_request_context('/?file="abc"',method='GET'):
            r = h.dispatch_request()
            print(r)
            self.assertDictContainsSubset({'payload':expectedData}, r[0])
            self.assertEqual(r[1], 200)

    def test_get_secondChunk(self):
        data = bytearray([1] * 251)
        data[250] = 0xee
        expectedData = base64.b64encode(b'\xee').decode("UTF-8")
        app = Flask(__name__)
        reader = Mock(spec=FileReader)
        reader.read.return_value = data

        h = handler.DownloadHandler(fileReader = reader)
        with app.test_request_context('/?file="abc"&chunk=2',method='GET'):
            r = h.dispatch_request()
            self.assertDictContainsSubset({'payload':expectedData,'chunk_num':2}, r[0])
            self.assertEqual(r[1], 200)
