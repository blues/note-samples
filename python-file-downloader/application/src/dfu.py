from notecard import hub
from time import time, sleep
import base64
import hashlib


class dfuInterface:

    def Open(self):
        pass

    def Close(self):
        pass

    def Read(self, start, length):
        pass




class dfuReader(dfuInterface):
    OpenTimeoutSec = 120

    _getTimeSec = time
    _sleep = sleep


    def __init__(self, card):
        self.NCard = card

    def Open(self): #, getTimeSecFn = time, sleepFn = sleep):
        self._requestDfuModeEntry()
        success = self._waitForDfuMode()
        if not success:
            self._requestDfuModeExit()
            raise(Exception("Notecard failed to enter DFU mode"))

        
    def Close(self):
        self._requestDfuModeExit()

    def Read(self, start=0,length=4096,num_retries=5):
        c = None
        
        for _ in range(num_retries):
            c = self._requestDfuChunk(start, length)
            if c != None:
                return c
    
        raise(Exception(f"Failed to read content after {num_retries} retries"))
        


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
            self._sleep(DFU_MODE_QUERY_RETRY_SEC)

        return False

    def _requestDfuChunk(self, start, length):
        rsp = self.NCard.Transaction({"req":"dfu.get","offset":start,"length":length})

        if "err" in rsp:
            return None

        if "payload" not in rsp:
            raise Exception(f"No content available at {start} with length {length}")

        content = base64.b64decode(rsp["payload"])

        expectedMD5 = rsp["status"]
        md5 = hashlib.md5(content).hexdigest()
        if md5 != expectedMD5:
            return None

        return content
    


GET_TIME_SEC = time
SLEEP = sleep

DFU_MODE_QUERY_RETRY_SEC = 2.5

def setTimeFunc(f):
    global GET_TIME_SEC
    GET_TIME_SEC = f


def resetTimeFunc():
    global GET_TIME_SEC
    GET_TIME_SEC = time

def fileAvailable(card):
    r = card.Transaction({"req":"dfu.status"})
    if "err" in r:
        raise Exception("Notecard returned error: " + r["err"])

    isAvailable = r["mode"] == "ready"
    return isAvailable

def getFileInfo(card):

    r = card.Transaction({"req":"dfu.status"})

    if "err" in r:
        raise Exception("Notecard returned error: " + r["err"])

    if r["mode"] != "ready":
        return None

    return r["body"]


def exitDFUMode(card):
    
    hub.set(card,mode="dfu-completed",sync=None)

def enterDFUMode(card,timeout_sec=120):
    hub.set(card,mode="dfu",sync=None)

    T = GET_TIME_SEC() + timeout_sec
    while GET_TIME_SEC() < T:
        r = card.Transaction({"req":"dfu.get"})
        if "err" not in r:
            return
        SLEEP(DFU_MODE_QUERY_RETRY_SEC)

    exitDFUMode(card)

    raise Exception("Notecard failed to enter DFU mode")


def getFileChunk(card, length=0, offset=0, num_retries=5):
    req = {"req":"dfu.get","offset":offset,"length":length}

    for _ in range(num_retries):
        rsp = card.Transaction(req)
        if "err" in rsp:
            continue

        if "payload" not in rsp:
            raise Exception("No content available file chunk at {offset} with length {length}")

        content = base64.b64decode(rsp["payload"])

        expectedMD5 = rsp["status"]
        md5 = hashlib.md5(content).hexdigest()
        if md5 != expectedMD5:
            continue

        return content

    raise Exception("Failed to get file chunk at {offset} with length {length}")




