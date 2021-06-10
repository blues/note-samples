import unittest
from server import reader

import os, tempfile
def getTestAssetPath():
    thisPath = os.path.dirname(__file__)
    #return os.path.join(thisPath, assetPath)
    return thisPath

class TestFileContent:                                                                                                  
    def __init__(self, content):                                                                                        

        self.file = tempfile.NamedTemporaryFile(mode='wb', delete=False)                                                 

        with self.file as f:                                                                                            
            f.write(content)                                                                                            

    @property                                                                                                           
    def fullname(self):                                                                                                 
        return self.file.name
    
    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def filepath(self):
        return os.path.dirname(self.file.name)

    def __enter__(self):                                                                                                
        return self                                                                                                     

    def __exit__(self, type, value, traceback):                                                                         
        os.unlink(self.fullname)     




class TestFileReader(unittest.TestCase):

        

    def test_constructor_hasDefaultProperties(self):
        f = reader.FileReader()
        self.assertEqual(f.asset_path, '.')
    
    def test_constructor_setAssetPath(self):
        f = reader.FileReader(asset_path = 'abc')
        self.assertEqual(f.asset_path, 'abc')

    def test_read_returnFileContent(self):
        fc = b'hello world'
        with TestFileContent(fc) as test_file:
            f = reader.FileReader(asset_path = test_file.filepath)
            c = f.read(test_file.filename)
            self.assertEqual(c, fc)




