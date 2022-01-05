BLOCK_LENGTH_BYTES = 512
HEADER_LENGTH_BYTES = BLOCK_LENGTH_BYTES

class TarFile:
    
    def __init__(self, f):
        self.f = open(f, 'rb') if isinstance(f, str) else f
        self._current_item = None
    
    def _readHeader(self):
        
        buf = self.f.read(HEADER_LENGTH_BYTES)
        offset = self.f.tell()

        h = getHeaderContentFromBuffer(buf)

        isHeaderEmpty = h.name[0] == 0
        if isHeaderEmpty:
            return None

        name = str(h.name,'utf-8').rstrip('\0')
        lastChar = name[-1]
        f_type = Type.DIR if lastChar == '/' else Type.FILE
        length = int(bytes(h.size), 8)
        return TarItem(self.f, name,f_type, length, offset)

    def __next__(self):

        if self._current_item:
            self.f.seek(self._current_item.BlockEnd)

        self._current_item = self._readHeader()

        if self._current_item is None:
            raise StopIteration

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
        self._start = start
        self._bytes_remaining = length
        self._block_length_bytes = blockLength
        self._isFirst = True

    def __next__(self):
        if self._bytes_remaining <= 0:
            raise StopIteration
            
        if self._isFirst:
            self._isFirst = False
            return self

        self._start += self._block_length_bytes
        self._bytes_remaining -= self._block_length_bytes

        if self._bytes_remaining <= 0:
            raise StopIteration
        
        return self

    def __iter__(self):
        self._isFirst = True
        return self

    def read(self):

        self._io.seek(self._start)
        numBytesToRead = self._bytes_remaining if self._bytes_remaining < self._block_length_bytes else self._block_length_bytes

        return self._io.read(numBytesToRead)

    def readinto(self, buffer):

        numBytesToRead = self._bytes_remaining if self._bytes_remaining < self._block_length_bytes else self._block_length_bytes
        if len(buffer) > numBytesToRead:
            buffer = memoryview(buffer)[0:numBytesToRead]

        self._io.seek(self._start)

        return self._io.readinto(buffer)



        






class Type:
    FILE=0
    DIR=1


# import uctypes

# # http://www.gnu.org/software/tar/manual/html_node/Standard.html
# 


import sys
use_micropython = sys.implementation.name == 'micropython'
if use_micropython:
    import uctypes
    TAR_HEADER = {
            "name": (uctypes.ARRAY | 0,   uctypes.UINT8 | 100),
            "size": (uctypes.ARRAY | 124, uctypes.UINT8 | 11),
        }
    def getHeaderContentFromBuffer(buf):
        return uctypes.struct(uctypes.addressof(buf), TAR_HEADER, uctypes.LITTLE_ENDIAN)
else:
    import struct
    S = struct.Struct('<100s24x11s')
    class headerContent:
        def __init__(self, name, size):
            self.name = name
            self.size = size

    def getHeaderContentFromBuffer(buf):
        n, s = S.unpack_from(buf, 0)
        return headerContent(n, s)


