from time import time, sleep
import binascii
import hashlib


class dfuReader:
    OpenTimeoutSec = 120

    _getTimeSec = time
    _sleep = sleep

    _offset = 0
    _length = 0
    _imageHash = None
    _md5 = hashlib.md5()

    def __init__(self, card, info=None):
        self.NCard = card

        if info is None:
            info = getUpdateInfo(self.NCard)

        self._length = info["length"]
        self._imageHash = info.get("md5", None)
            
        
        


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def reset(self):
        self._offset = 0
        self._md5 = hashlib.md5()


    def close(self):
        exitDFUMode(self.NCard)

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
                c = _requestDfuChunk(self.NCard, self._offset, size)
                break
            except Exception as e:
                requestException = e

        if requestException is not None:
            raise Exception(
                f"Failed to read content after {num_retries} retries") from requestException

        self._md5.update(c)
        self._offset += size
        return c

    def read_to_writer(self, writer, size=4096, num_retries=5):

        c = self.read(size=size, num_retries=num_retries)
        if c == None:
            return 0

        length = writer.write(c)
        return length

    def GetInfo(self):
        return getUpdateInfo(self.NCard)

    def get_hash(self):
        return self._md5.hexdigest()

    def check_hash(self):
        return (self.get_hash() == self._imageHash)

def _cardTransactionFailsOnNotecardErrorMessage(card, req, messageHeader='Notecard returned error'):

    rsp = card.Transaction(req)

    if "err" in rsp:
        raise Exception(f'{messageHeader}: {rsp["err"]}')

    return rsp


DFU_MODE_QUERY_RETRY_SEC = 2.5


def isUpdateAvailable(card):
    r = _cardTransactionFailsOnNotecardErrorMessage(
        card, {"req": "dfu.status"})

    if "mode" not in r:
        return False

    isAvailable = r["mode"] == "ready"
    return isAvailable


def getUpdateInfo(card):

    r = _cardTransactionFailsOnNotecardErrorMessage(
        card, {"req": "dfu.status"})

    if "mode" not in r:
        return None

    if r["mode"] != "ready":
        return None

    return r["body"]


def enterDFUMode(card):
    _cardTransactionFailsOnNotecardErrorMessage(card, {"req":"hub.set","mode":"dfu"}, messageHeader='Notecard request for DFU mode entry failed' )


def exitDFUMode(card):
    _cardTransactionFailsOnNotecardErrorMessage(card, {"req":"hub.set","mode":"dfu-completed"}, messageHeader='Notecard request for DFU mode exit failed' )

def isDFUModeActive(card):
    rsp = card.Transaction({"req":"dfu.get"})
    return "err" not in rsp

def setUpdateDone(card, message):
    req = {"req": "dfu.status",
           "stop": True,
           "status": message}
    _cardTransactionFailsOnNotecardErrorMessage(card, req)


def setUpdateError(card, message):
    req = {"req": "dfu.status",
           "stop": True,
           "err": message,
           "status": message}
    _cardTransactionFailsOnNotecardErrorMessage(card, req)


def enableUpdate(card):
    _cardTransactionFailsOnNotecardErrorMessage(card,
                                                {"req": "dfu.status", "on": True})


def disableUpdate(card):
    _cardTransactionFailsOnNotecardErrorMessage(card,
                                                {"req": "dfu.status", "off": True})


def setVersion(card, version):
    _cardTransactionFailsOnNotecardErrorMessage(card,
                                                {"req": "dfu.status", "version": version})

def _requestDfuChunk(card, start, length):

        rsp = _cardTransactionFailsOnNotecardErrorMessage(card, 
            {"req":"dfu.get","offset":start,"length":length})

        if "payload" not in rsp:
            raise Exception(f"No content available at {start} with length {length}")

        content = binascii.a2b_base64(rsp["payload"])

        expectedMD5 = rsp["status"]
        md5 = hashlib.md5(content).hexdigest()
        if md5 != expectedMD5:
            raise Exception ("content checksum mismatch")

        return content

def _getTimeMS():
    return int(time()*1000)

def _sleepMS(p):
    sleep(p/1000)

def waitForDFUMode(card, timeoutMS = 120000, getTimeMS = _getTimeMS, retryPeriodMS = DFU_MODE_QUERY_RETRY_SEC, sleepMS = _sleepMS):
    t = getTimeMS() + timeoutMS
    
    while (not isDFUModeActive(card)):
        if getTimeMS() > t:
            raise Exception("timed out waiting for DFU mode")
        sleepMS(retryPeriodMS)

def open(card):
    
    enterDFUMode(card)
    waitForDFUMode(card)

    return dfuReader(card)

def copyImageToWriter(card, writer, size=4096, reader=None, progressUpdater=lambda m: None):

    with open(card) as r:
        numBytesWritten = 1
        totalBytesWritten = 0
        n = r._length
        r.seek(0)
        while numBytesWritten > 0:
            numBytesWritten = r.read_to_writer(writer, size=size)
            totalBytesWritten += numBytesWritten
            progressUpdater(int(totalBytesWritten * 100 / n))

        if not r.check_hash():
            raise Exception('Image hash mismatch')
