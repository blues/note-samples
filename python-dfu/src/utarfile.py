BLOCK_LENGTH_BYTES = 512
HEADER_LENGTH_BYTES = BLOCK_LENGTH_BYTES

import os



def extractAll(f, rootFolder = ""):
    t = TarExtractor(fileName=f, rootFolder=rootFolder)

    while t.extractNext():
        pass

class TarExtractor:
        
    def __init__(self, fileName="", rootFolder="") -> None:
        self.FileName = fileName
        self.RootFolder = rootFolder
        self._mkdir = os.mkdir

        

        self._tarFile = TarFile(self.FileName) if self.FileName != "" else None

    def extractNext(self) -> bool:

        if self._tarFile is None:
            raise(Exception("TAR file not defined"))

        hasMore = True
        isDone = False
        try:
            i = next(self._tarFile)
        except StopIteration:
            return isDone

        if i.Type is Type.DIR:
            self._writeTarItemAsDir(i)
            return hasMore
        
        self._writeTarItemAsFile(i)
        return hasMore

    def openFile(self, fileName) -> None:
        self.FileName = fileName
        self._tarFile = TarFile(self.FileName)
        

    def _writeTarItemAsFile(self, item):
        n = item.Name if self.RootFolder == "" else self.RootFolder + "/" + item.Name
        with open(n, "wb") as f: # type: ignore
            buf = bytearray(BLOCK_LENGTH_BYTES)
            for b in item.Blocks:
                numBytes = b.readinto(buf)
                f.write(buf[0:numBytes])
                
    def _writeTarItemAsDir(self,item):
        n = item.Name if self.RootFolder == "" else self.RootFolder + "/" + item.Name
        self._mkdir(n)



class TarFile:
    
    def __init__(self, f):
        self.f = open(f, 'rb') if isinstance(f, str) else f # type: ignore
        self._current_item = None
    
    def _readHeader(self):
        
        buf = self.f.read(HEADER_LENGTH_BYTES)
        offset = self.f.tell()

        h = getHeaderContentFromBuffer(buf)

        isHeaderEmpty = h.name[0] == 0 # type: ignore
        if isHeaderEmpty:
            return None

        name = str(h.name,'utf-8').rstrip('\0') # type: ignore
        lastChar = name[-1]
        f_type = Type.DIR if lastChar == '/' else Type.FILE
        length = int(bytes(h.size), 8) # type: ignore
        return TarItem(self.f, name,f_type, length, offset)

    def __next__(self):

        if self._current_item:
            self.f.seek(self._current_item.BlockEnd)

        i = self._readHeader()

        if i is None:
            raise StopIteration

        self._current_item = i

        return self._current_item

    def __iter__(self):
        self._current_item = None
        return self

class TarItem:
    def __init__(self, io, name, type, length, offset):
        self._io = io
        self.Name = name
        self.Type = type
        self.Length = length
        self.Start = offset
        self.End = offset + length
        self.BlockEnd = offset + ((length + BLOCK_LENGTH_BYTES -1) & ~(BLOCK_LENGTH_BYTES - 1))

        self.Blocks = None if self.Type == Type.DIR else TarBlock(self._io, self.Start, self.Length)
        



    def read(self):
        self._io.seek(self.Start)
        return self._io.read(self.Length)

    def readinto(self, buffer):

        if len(buffer) > self.Length:
            buffer = memoryview(buffer)[0:self.Length]
        
        self._io.seek(self.Start)
        return self._io.readinto(buffer)

class TarBlock:
    def __init__(self, io, start, length, blockLength=BLOCK_LENGTH_BYTES):
        self._io = io
        self.Start = start
        self.Length = length
        self._current_position = -1
        self._bytes_remaining = length
        self._block_length_bytes = blockLength

    def __next__(self):
        if self._bytes_remaining <= 0:
            raise StopIteration
            
        if self._current_position < 0:
            self._current_position = self.Start
            return self

        self._current_position += self._block_length_bytes
        self._bytes_remaining -= self._block_length_bytes

        if self._bytes_remaining <= 0:
            raise StopIteration
        
        return self

    def __iter__(self):
        self._current_position = -1
        self._bytes_remaining = self.Length
        return self

    def read(self):
        
        numBytesToRead = self._bytes_remaining if self._bytes_remaining < self._block_length_bytes else self._block_length_bytes
        
        p = self._current_position if self._current_position >=0 else self.Start
        self._io.seek(p)
        return self._io.read(numBytesToRead)

    def readinto(self, buffer):

        numBytesToRead = self._bytes_remaining if self._bytes_remaining < self._block_length_bytes else self._block_length_bytes
        if len(buffer) > numBytesToRead:
            buffer = memoryview(buffer)[0:numBytesToRead]

        p = self._current_position if self._current_position >=0 else self.Start
        self._io.seek(p)

        return self._io.readinto(buffer)



        






class Type:
    FILE=0
    DIR=1




# # http://www.gnu.org/software/tar/manual/html_node/Standard.html
# 

def getHeaderContentFromBuffer(buf): # pragma: no cover
    pass


import sys
use_micropython = sys.implementation.name == 'micropython' # type: ignore
if use_micropython: # pragma: no cover
    import uctypes
    TAR_HEADER = {
            "name": (uctypes.ARRAY | 0,   uctypes.UINT8 | 100),
            "size": (uctypes.ARRAY | 124, uctypes.UINT8 | 11),
        }
    def getHeaderContentFromBufferMP(buf):
        return uctypes.struct(uctypes.addressof(buf), TAR_HEADER, uctypes.LITTLE_ENDIAN)
    getHeaderContentFromBuffer = getHeaderContentFromBufferMP  # type: ignore
else:
    import struct
    S = struct.Struct('<100s24x11s')  # type: ignore
    class headerContent:
        def __init__(self, name, size):
            self.name = name
            self.size = size

    def getHeaderContentFromBufferCP(buf):
        n, s = S.unpack_from(buf, 0)
        return headerContent(n, s)

    getHeaderContentFromBuffer = getHeaderContentFromBufferCP  # type: ignore

