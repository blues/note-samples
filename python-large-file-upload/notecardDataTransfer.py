from notecard import binary_helpers
import time
import io


DEFAULT_WEB_TRANSACTION_TIMEOUT_SEC = 30


class BinaryDataUploader:

    webReqRoot = {"req":"web.post",
                "seconds": DEFAULT_WEB_TRANSACTION_TIMEOUT_SEC,
                "binary":True,
                "route": '',
                "offset":0,
                "total":0
                }
    
    ConnectionTimeoutSeconds = 90

    def __init__(self, card, route, timeout=DEFAULT_WEB_TRANSACTION_TIMEOUT_SEC, printFcn=print, waitForNotehubConnection=True, setTempContinuousMode=True) -> None:
        self._card = card
        self._print = printFcn
        self.WaitForConnection = waitForNotehubConnection
        self.SetTemporaryContinuousMode=setTempContinuousMode
        self.webReqRoot['route'] = route
        self.webReqRoot['seconds'] = timeout
        

    def upload(self, data:io.BytesIO):
        if self.SetTemporaryContinuousMode:
            self._setTempContinuousMode()
        
        if self.WaitForConnection:
            self._print(f"Waiting for Notehub connection")
            self._waitForConnection()

        self._writeAndFlushBytes(data)

        if self.SetTemporaryContinuousMode:
            self._unsetTempContinuousMode()

    ## Notecard Request Method
    def _sendRequest(self, req, args=None, errRaisesException=True):
        if isinstance(req,str):
            req = {"req":req}

        if args:
            req = dict(req, **args)

        self._print(req)
        rsp = self._card.Transaction(req)
        self._print(rsp)
        if errRaisesException and 'err' in rsp:
            raise Exception("Notecard Transaction Error: " + rsp['err'])

        return rsp
        
    def _writeWebReqBinary(self, offset, total):
        webReq = self.webReqRoot
        webReq['offset'] = offset
        webReq['total'] = total
        rsp = self._sendRequest(webReq)

        if rsp.get("result", 300) >= 300:
            msg = rsp.get('body', {}).get('err', 'unknown')
            raise Exception("Web Request Error: " + msg)



    def _writeAndFlushBytes(self, data: io.IOBase):
        
        totalBytes = data.seek(0,2)
        data.seek(0,0)

        bytesSent = 0
        while bytesSent < totalBytes:
            binary_helpers.binary_store_reset(self._card)
            rsp = self._sendRequest("card.binary")
            max = rsp.get("max", 0)
            
            buffer = bytearray(max)
            numBytes = data.readinto(buffer)

            binary_helpers.binary_store_transmit(self._card, buffer[0:numBytes], 0)
            
            self._writeWebReqBinary(bytesSent, totalBytes)

            bytesSent += numBytes


    def _waitForConnection(self):
        startTime = time.time()
        isConnected=False
        while not isConnected:
            if (time.time() - startTime) > self.ConnectionTimeoutSeconds:
                raise(Exception(f"Timeout of {self.ConnectionTimeoutSeconds} seconds expired while waiting to connect to Notehub"))
            
            rsp = self._sendRequest("hub.status")
            isConnected =  rsp.get('connected', False)
            time.sleep(1)

    def _setTempContinuousMode(self):
        timeoutSecs = 3600
        req = {"req":"hub.set", "on":True, "seconds":timeoutSecs}
        self._sendRequest(req)

    def _unsetTempContinuousMode(self):
        req = {"req":"hub.set", "off":True}
        self._sendRequest(req)


import binascii
class BinaryDataUploaderLegacy(BinaryDataUploader):
    webReqRoot = {"req":"web.post",
                "seconds": DEFAULT_WEB_TRANSACTION_TIMEOUT_SEC,
                "payload": '',
                "route": '',
                "offset":0,
                "total":0
                }
    chunk_size = 1024
    def upload(self, data:io.BytesIO):
        if self.SetTemporaryContinuousMode:
            self._setTempContinuousMode()
        
        if self.WaitForConnection:
            self._print(f"Waiting for Notehub connection")
            self._waitForConnection()

        self._sendBytesBase64Payload(data)

        if self.SetTemporaryContinuousMode:
            self._unsetTempContinuousMode()

    def _sendBytesBase64Payload(self, data: io.IOBase):
        buffer = bytearray(self.chunk_size)

        totalBytes = data.seek(0,2)
        data.seek(0,0)

        bytesSent = 0
        while bytesSent < totalBytes:
            numBytes = data.readinto(buffer)

            self._writeWebReqPayload(buffer[0:numBytes], bytesSent, totalBytes)

            bytesSent += numBytes

    def _writeWebReqPayload(self, payload, offset, total):
        webReq = self.webReqRoot
        webReq['payload'] = str(binascii.b2a_base64(bytes(payload))[:-1], 'utf-8')
        webReq['offset'] = offset
        webReq['total'] = total
        rsp = self._sendRequest(webReq)

        if rsp.get("result", 300) >= 300:
            msg = rsp.get('body', {}).get('err', 'unknown')
            raise Exception("Web Request Error: " + msg)

