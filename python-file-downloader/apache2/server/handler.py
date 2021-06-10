from flask_restful import Resource
from webargs import fields, validate
from webargs.flaskparser import use_kwargs, parser, abort

from reader import FileReader

from encode import chunkAsBase64


class DownloadHandler(Resource):

    def __init__(self,fileReader=FileReader()) -> None:

        super().__init__()
        self._fileReader=fileReader


    args = {
             "file": fields.Str(required=True,help='Name of file to be downloaded'),
             "chunk": fields.Int(missing=1, validate=validate.Range(min=1), help='Chunk number to download (defaults to 1)')
           }
    @use_kwargs(args,location='query')
    def get(self, file, chunk):

        try:
            
            content = self._fileReader.read(file)
            
            r = chunkAsBase64(content,chunk)
            d = {'payload':r["data"],
                    'chunk_num':r["chunk_num"],
                    'total_chunks':r["total_chunks"],
                    'crc32':r["crc32"]}
            return d, 200
        except:
            return({'message':'internal server error'},400)



@parser.error_handler
def handle_request_parsing_error(err, req, schema, *, error_status_code, error_headers):
    """webargs error handler that uses Flask-RESTful's abort function to return
    a JSON error response to the client.
    """
    #abort(error_status_code, errors=err.messages)
    print(req)
    print(schema)
    print(error_status_code)
    print(error_headers)
    print(err.messages)
    abort(error_status_code, errors=err.messages)