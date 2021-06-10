

import os

class FileReader:

    asset_path = '.'
    def __init__(self, asset_path='.') -> None:
        self.asset_path=asset_path

    def read(self, filename):
        p = os.path.join(self.asset_path, filename)
        print(p)        
        with open(p, 'rb') as f:
            c = f.read()
            return(c)