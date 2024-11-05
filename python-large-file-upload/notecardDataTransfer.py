from notecard import binary_helpers
import time
import io


DEFAULT_WEB_TRANSACTION_TIMEOUT_SEC = 30
DEFAULT_CARD_WEB_REQUEST = "web.post"
DEFAULT_MS_AZURE_FILENAME = "datafile"

class BinaryDataUploader:

    webReqRoot = {"req":DEFAULT_CARD_WEB_REQUEST,
                "seconds": DEFAULT_WEB_TRANSACTION_TIMEOUT_SEC,
                "content":"application/octet-stream",
                "binary":True,
                "route": '',
                "offset":0,
                "total":0
                }

    ConnectionTimeoutSeconds = 90

    def __init__(self, card, req, route, timeout=DEFAULT_WEB_TRANSACTION_TIMEOUT_SEC, printFcn=print, waitForNotehubConnection=True, setTempContinuousMode=True) -> None:
        self._card = card
        self._print = printFcn
        self.WaitForConnection = waitForNotehubConnection
        self.SetTemporaryContinuousMode=setTempContinuousMode
        self.webReqRoot['req'] = req
        self.webReqRoot['route'] = route
        self.webReqRoot['seconds'] = timeout
        self._fileName = None
        self._binaryBuffSize = None
        self._cloud_service = None

    def setFileNameViaEnvDefault(self, fileName):
        """
        Set the filename via the env.default method

        This method is needed for cloud providers such as Microsoft Azure, where the filename
        cannot be set via a web request. Instead, the filename must be set via the env.default
        method. For this to work, the route URL in notehub must have a $filename placeholder in
        it. For more information, check doc/azure.md
        """

        # Get the current sync time
        rsp = self._sendRequest("hub.sync.status")
        lastSyncTime = currentSyncTime = rsp.get('time', 0)

        # Get the filename and env update time
        envReq = {"req":"env.get"}
        rsp = self._sendRequest(envReq)
        existingFilename = rsp.get("body", {}).get("filename", None)
        envUpdateTime = rsp.get("time", 0)

        # Only sync if the filename is different or the last sync time is older than the env update time
        if existingFilename != fileName or lastSyncTime < currentSyncTime:
            # Set the filename via env.default and force a sync to update the value on Notehub
            envReq = {"req":"env.default", "name":"filename", "text":fileName}
            rsp = self._sendRequest(envReq)
            rsp = self._sendRequest("hub.sync")

            # Wait for the sync to complete
            startTime = time.time()
            while currentSyncTime <= lastSyncTime:
                if (time.time() - startTime) > self.ConnectionTimeoutSeconds:
                    raise TimeoutError(f"Timeout of {self.ConnectionTimeoutSeconds} " +
                                    "seconds expired while waiting to sync env.default")

                rsp = self._sendRequest("hub.sync.status")
                currentSyncTime =  rsp.get('time', currentSyncTime)
                time.sleep(1)

    def setFileName(self, fileName):
        self._fileName = fileName

    def unsetFileName(self):
        self._fileName = None

    def upload(self, data:io.BytesIO, unsetFileName=True):
        if self.SetTemporaryContinuousMode:
            self._setTempContinuousMode()

        if self.WaitForConnection:
            self._print(f"Waiting for Notehub connection")
            self._waitForConnection()

        if self._cloud_service == "azure":
            # Due to a limitation in MS Azure where the filename cannot be set via a web request,
            # the filename is instead set via the env.default method. This means that the filename
            # must be set before the data is uploaded to Notehub. If the filename is not set, the
            # default filename is used. For more info, check setFileNameViaEnvDefault().
            if self._fileName is None:
                self._fileName = DEFAULT_MS_AZURE_FILENAME
            self.setFileNameViaEnvDefault(self._fileName)

        self._writeAndFlushBytes(data)

        if self.SetTemporaryContinuousMode:
            self._unsetTempContinuousMode()

        if unsetFileName:
            self.unsetFileName()

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
        # If the filename is set, add it to the web request. This is not supported for Azure
        # which doesn't have a filename field in the web request, and adding it will cause an error
        if (self._fileName is not None) and (self._cloud_service != "azure"):
            webReq['name'] = self._fileName

        rsp = self._sendRequest(webReq)

        if rsp.get("result", 300) >= 300:
            cobLength = rsp.get('cobs', 0)
            # if cobLength > 0:
            #     y = binary_helpers.binary_store_receive(self._card, 0, cobLength)
            #     self._print(y)

            msg = rsp.get('body', {}).get('err', 'unknown')
            raise Exception("Web Request Error: " + msg)



    def _writeAndFlushBytes(self, data: io.IOBase):

        totalBytes = data.seek(0,2)
        data.seek(0,0)

        bytesSent = 0
        while bytesSent < totalBytes:
            binary_helpers.binary_store_reset(self._card)
            rsp = self._sendRequest("card.binary")

            # First set the buffer size to be equal to the max binary buffer size supported by the notecard,
            # then check if the user has specified a smaller buffer size through the -B/--binary-size flag
            buffSize = rsp.get("max", 0)
            if self._binaryBuffSize is not None:
                buffSize = min(self._binaryBuffSize, buffSize)

            # Create a buffer of the specified size
            buffer = bytearray(buffSize)

            # Read the data from the file and store it in the notecard's binary store
            numBytes = data.readinto(buffer)
            binary_helpers.binary_store_transmit(self._card, buffer[0:numBytes], 0)

            # Send the binary data to notehub
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

    def setBinaryBuffSize(self, binaryBuffSize):
        self._binaryBuffSize = binaryBuffSize

    def setCloudService(self, cloudService):
        self._cloud_service = cloudService

import binascii
class BinaryDataUploaderLegacy(BinaryDataUploader):
    webReqRoot = {"req":DEFAULT_CARD_WEB_REQUEST,
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

