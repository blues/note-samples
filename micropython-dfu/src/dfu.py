from time import time, sleep
import binascii
import sys
if sys.implementation.name == 'cpython': # type: ignore
    import hashlib
else :
    import hashlibextras as hashlib # type: ignore

class dfuReader:
    OpenTimeoutSec = 120

    _getTimeSec = time
    _sleep = sleep

    _offset = 0
    _length = 0
    _imageHash = None
    _md5 = hashlib.md5() # type: ignore

    def __init__(self, card):
        self.NCard = card

    def Open(self):
        self._requestDfuModeEntry()
        success = self._waitForDfuMode()
        if not success:
            self._requestDfuModeExit()
            raise(Exception("Notecard failed to enter DFU mode"))

        info = self.GetInfo()
        self._length = info["length"] # type: ignore
        self._imageHash = info.get("md5",None) # type: ignore


        self._md5 = hashlib.md5() # type: ignore

        self.seek(0)

        
    def Close(self):
        self._requestDfuModeExit()

    def readable(self):
        return True

    def writable(self):
        return False

    def seek(self, v):
        self._offset = v

    def read(self, size=4096, num_retries=5):

        if self._offset + size > self._length:
            size = self._length - self._offset
        
        if size <= 0:
            return None

        c = b''
        requestException = None
        for _ in range(num_retries):
            requestException = None
            try:
                c = self._requestDfuChunk(self._offset, size)
                break
            except Exception as e:
                requestException = e

        if requestException != None:
            raise Exception(f"Failed to read content after {num_retries} retries") from requestException

        self._md5.update(c)
        self._offset += size
        return c
    
        

    def read_to_writer(self, writer, size = 4096, num_retries=5):

        c = self.read(size=size, num_retries=num_retries)
        if c == None:
            return 0

        length = writer.write(c)
        return length
    
    def GetInfo(self):
        return getUpdateInfo(self.NCard)

    def reset_hash(self):
        self._md5 = hashlib.md5() # type: ignore

    def get_hash(self):
        return self._md5.hexdigest()

    def check_hash(self):
        return (self.get_hash() == self._imageHash)

    def _requestDfuModeEntry(self):
        rsp = self.NCard.Transaction({"req":"hub.set","mode":"dfu"})
        if "err" in rsp:
            raise Exception(f"Notecard request for DFU mode entry failed: {rsp['err']}")


    def _requestDfuModeExit(self):
        rsp = self.NCard.Transaction({"req":"hub.set","mode":"dfu-completed"})
        if "err" in rsp:
            raise Exception(f"Notecard request for DFU mode exit failed: {rsp['err']}")

    def _waitForDfuMode(self ):
        
        timeout_sec = self.OpenTimeoutSec
        
        expiry = self._getTimeSec() + timeout_sec
        while self._getTimeSec() < expiry:
            r = self.NCard.Transaction({"req":"dfu.get"})
            if "err" not in r:
                return True
            self._sleep(DFU_MODE_QUERY_RETRY_SEC) # type: ignore

        return False

    def _requestDfuChunk(self, start, length):

        req = {"req":"dfu.get","offset":start,"length":length}
        rsp = self.NCard.Transaction(req)

        if "err" in rsp:
            m = f"Notecard returned error: " + rsp["err"]
            raise Exception(m)

        if "payload" not in rsp:
            raise Exception(f"No content available at {start} with length {length}")

        content = binascii.a2b_base64(rsp["payload"])

        expectedMD5 = rsp["status"]
        md5 = hashlib.md5(content).hexdigest() # type: ignore
        if md5 != expectedMD5:
            raise Exception ("content checksum mismatch")

        return content

def _cardTransactionFailsOnNotecardErrorMessage(card, req):

    rsp = card.Transaction(req)
    
    if "err" in rsp:
        raise Exception(f'Notecard returned error: {rsp["err"]}')

    return rsp


    
DFU_MODE_QUERY_RETRY_SEC = 2.5

def isUpdateAvailable(card):
    r = _cardTransactionFailsOnNotecardErrorMessage(card, {"req":"dfu.status"})

    if "mode" not in r:
        return False

    isAvailable = r["mode"] == "ready"
    return isAvailable

def getUpdateInfo(card):

    r = _cardTransactionFailsOnNotecardErrorMessage(card,{"req":"dfu.status"})

    if "mode" not in r:
        return None

    if r["mode"] != "ready":
        return None

    return r["body"]

def setUpdateDone(card, message):
    req = {"req":"dfu.status",
          "stop": True,
          "status":message}
    _cardTransactionFailsOnNotecardErrorMessage(card,req)

def setUpdateError(card, message):
    req = {"req":"dfu.status",
          "stop": True,
          "err":message,
          "status":message}
    _cardTransactionFailsOnNotecardErrorMessage(card,req)

def enableUpdate(card):
    _cardTransactionFailsOnNotecardErrorMessage(card, 
                    {"req":"dfu.status","on": True})


def disableUpdate(card):
    _cardTransactionFailsOnNotecardErrorMessage(card, 
                    {"req":"dfu.status","off":True})

def setVersion(card, version):
    _cardTransactionFailsOnNotecardErrorMessage(card,
                    {"req":"dfu.status","version":version})


class _dfuReader_ContextManager(object):
    def __init__(self, reader):
        self.reader = reader
    
    def __enter__(self):
        self.reader.Open()
        return self.reader

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.reader.Close()

def openDfuForRead(card, reader=None):
    if reader==None:
        reader = dfuReader(card)
    
    return _dfuReader_ContextManager(reader)


def copyImageToWriter(card, writer, size=4096, reader=None,progressUpdater=lambda m:None):

    with openDfuForRead(card, reader=reader) as r:
        numBytesWritten = 1
        totalBytesWritten = 0
        n = r._length
        r.seek(0)
        while numBytesWritten > 0:
            numBytesWritten = r.read_to_writer(writer,size=size)
            totalBytesWritten += numBytesWritten
            progressUpdater(int(totalBytesWritten * 100 / n))

        if not r.check_hash():
            raise Exception('Image hash mismatch')


