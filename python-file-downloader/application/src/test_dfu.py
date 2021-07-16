
import os
import sys
import notecard
import json
import pytest
import hashlib
import base64

import dfu

from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..')))

def createNotecardAndPort():
    serial = Mock()  # noqa: F811
    port = serial.Serial("/dev/tty.foo", 9600)
    port.read.side_effect = [b'\r', b'\n', None]
    port.readline.return_value = "\r\n"
    port.write()

    nCard = notecard.OpenSerial(port)

    return (nCard, port)


def convertToSerialStr(r):
    if type(r) is dict:
        r = json.dumps(r)

    return r + "\r\n"

def setResponse(port, response):

    port.readline.return_value = convertToSerialStr(response)

def setResponseList(port, response):

    if type(response) is not list:
        response = [response,]

    s = []
    for r in response:
        s.append(convertToSerialStr(r))

    

    port.readline.side_effect =  s


def createReaderAndPort():
    nCard, port = createNotecardAndPort()
    r = dfu.dfuReader(nCard)
    return (r, port)

def createReaderWithMockTimersAndPort():
    r, port = createReaderAndPort()
    timerFn = Mock()
    sleepFn = Mock()
    r._getTimeSec = timerFn
    r._sleep = sleepFn

    return (r, port)


def test_dfuReader_constructor_hasDefaultPropertyValues():
    nCard, port = createNotecardAndPort()
    d = dfu.dfuReader(nCard)

    assert(dfu.dfuInterface in d.__class__.__bases__)
    assert(d.NCard == nCard)
    assert(d.OpenTimeoutSec == 120)



def test_dfuReader_Open_made_call_to_notecard():
    d, port = createReaderAndPort()
    setResponse(port, {})

    d.Open()

    calls = port.write.call_args_list

    req1 = json.loads(calls[2][0][0])
    assert req1["req"] == "hub.set"
    assert req1["mode"] == "dfu"


def test_dfuReader_Open_callsNotecard_errRaisesException():
    d, port = createReaderWithMockTimersAndPort()
    setResponse(port, {"err":"some error message"})

    with pytest.raises(Exception, match="Notecard request for DFU mode entry failed"):
        d.Open()


def test_dfuReader_Open_waitsForDfuMode():
    d, port = createReaderWithMockTimersAndPort()
    setResponse(port, {})
    d._getTimeSec.return_value = 0
    

    d.Open()

    calls = port.write.call_args_list

    req1 = json.loads(calls[3][0][0])
    assert req1["req"] == "dfu.get"
    

def test_dfuReader_Open_dfuModeTimesOut_raisesException():
    d, port = createReaderWithMockTimersAndPort()
    d._getTimeSec.side_effect = [0, 0, d.OpenTimeoutSec + 1]
    
    dfuGetErrorResponse = {"err":"abc"}
    dfuModeEntryResponse = {}
    dfuModeExitResponse = {}
    setResponseList(port, [dfuModeEntryResponse,dfuGetErrorResponse, dfuModeExitResponse])

    with pytest.raises(Exception, match="Notecard failed to enter DFU mode"):
        d.Open()

   
def test_dfuReader_Open_failsToEstablishDfuMode_ClosesDfuMode():
    d, port = createReaderAndPort()
    setResponse(port, "{}")
    f = Mock(return_value=False)
    d._waitForDfuMode = f
    d._requestDfuModeExit = Mock()

    with pytest.raises(Exception):
        d.Open()

    d._requestDfuModeExit.assert_called_once()
        
            

def test_dfuReader_Close_callsNotecard():
    d, port = createReaderAndPort()
    setResponse(port, {})

    d.Close()

    calls = port.write.call_args_list
    req1 = json.loads(calls[2][0][0])
    assert req1["req"] == "hub.set"
    assert req1["mode"] == "dfu-completed"


def test_dfuReader_Close_callsNotecard_failureRaisesException():
    d, port = createReaderAndPort()
    setResponse(port, {"err":"some error message"})

    with pytest.raises(Exception, match="Notecard request for DFU mode exit failed"):
        d.Close()

    

def test_dfuReader_Read_returnsFirstChunk():
    d, port = createReaderAndPort()
    content = b'here is my chunk content'
    payload = str(base64.b64encode(content), 'utf8')
    md5 = hashlib.md5(content).hexdigest()

    setResponse(port, {"payload":payload,"status":md5})

    c = d.Read(start=0)

    assert c == content


def test_dfuReader_Read_sendsRequestToNotecard():
    d, port = createReaderAndPort()
    content = b'here is my chunk content'
    payload = str(base64.b64encode(content), 'utf8')
    md5 = hashlib.md5(content).hexdigest()

    setResponse(port, {"payload":payload,"status":md5})

    start = 7
    length = 5
    c = d.Read(start=start,length=length)

    calls = port.write.call_args_list
    req1 = json.loads(calls[2][0][0])
    assert req1["req"] == "dfu.get"
    assert req1["offset"] == start
    assert req1["length"] == length

def test_dfuReader_Read_no_payload_raises_exception():
    d, port = createReaderAndPort()
    setResponse(port, {})
    start = 0
    length = 4096

    message = f"No content available at {start} with length {length}"
    with pytest.raises(Exception, match=message):
        c = d.Read(start=start,length=length)

def test_dfuReader_Read_recoversFromNotecardIoError():
    d, port = createReaderAndPort()
    content = b'here is my chunk content'
    payload = str(base64.b64encode(content), 'utf8')
    md5 = hashlib.md5(content).hexdigest()

    setResponseList(port, [{"err":"\{io\}"},{"payload":payload,"status":md5}])

    c = d.Read(start=0)

    assert c == content

def test_dfuReader_Read_tooManyFailedReadsRaisesException():
    d, port = createReaderAndPort()
    d._requestDfuChunk = Mock(return_value=None)

    num_retries = 2
    message = f"Failed to read content after {num_retries} retries"
    with pytest.raises(Exception, match=message):
        c = d.Read(num_retries=num_retries)

def test_dfuReader_Read_md5MismatchRaisesException():
    d, port = createReaderAndPort()
    content = b'here is my chunk content'
    payload = str(base64.b64encode(content), 'utf8')
    md5 = "abc"
    setResponse(port, {"payload":payload,"status":md5})
    
    num_retries = 2
    message = f"Failed to read content after {num_retries} retries"
    with pytest.raises(Exception, match=message):
        c = d.Read(num_retries=num_retries)

def test_fileAvailable_when_file_available():
    nCard, port = createNotecardAndPort()

    setResponse(port, {
        "mode":   "ready",
        "status": "successfully downloaded",
        })

    tf = dfu.fileAvailable(nCard)

    assert tf == True

def test_fileAvailable_when_not_available():

    nCard, port = createNotecardAndPort()

    setResponse(port, {"mode":   "idle"})

    tf = dfu.fileAvailable(nCard)

    assert tf == False

    setResponse(port, {"mode":   "downloading"})

    tf = dfu.fileAvailable(nCard)

    assert tf == False

    setResponse(port, {"mode":   "error"})

    tf = dfu.fileAvailable(nCard)

    assert tf == False

def test_fileAvailable_response_has_error():

    nCard, port = createNotecardAndPort()

    message = "something went wrong"
    setResponse(port, {
        "err": message
        })

    with pytest.raises(Exception, match="Notecard returned error: " + message):
        f = dfu.fileAvailable(nCard)


def test_getFileInfo_when_file_available():

    nCard, port = createNotecardAndPort()
    fileLength = 42892
    crc32 = 2525287425
    md5 = "5a3f73a7f1b4bc8917b12b36c2532969"
    name = "py-new-firmware$20200903200351.bin"
    source = "py-new-firmware.py"
    version = "abcd.efg"

    setResponse(port, {
        "mode": "ready",
        "status": "successfully downloaded",
        "on": True,
        "body": {
            "crc32": crc32,
            "created": 1599163431,
            "info": {},
            "length": fileLength,
            "md5": md5,
            "modified": 1599163431,
            "name": name,
            "notes": "Latest prod firmware",
            "source": source,
            "type": "firmware",
            "version": version,
        }
        })

    f = dfu.getFileInfo(nCard)

    
    assert f["length"] == fileLength
    assert f["crc32"] == crc32
    assert f["md5"] == md5
    assert f["name"] == name
    assert f["source"] == source


def test_getFileInfo_response_has_error():

    nCard, port = createNotecardAndPort()

    message = "something went wrong"
    setResponse(port, {
        "err": message
        })

    with pytest.raises(Exception, match="Notecard returned error: " + message):
        f = dfu.getFileInfo(nCard)



def test_getFileInfo_when_not_available():

    nCard, port = createNotecardAndPort()

    setResponse(port, {"mode":   "idle"})

    f = dfu.getFileInfo(nCard)

    assert f == None

    setResponse(port, {"mode":   "downloading"})

    f = dfu.getFileInfo(nCard)

    assert f == None

    setResponse(port, {"mode":   "error"})

    f = dfu.getFileInfo(nCard)

    assert f == None


def test_exitDFUMode():
    nCard, port = createNotecardAndPort()
    setResponse(port, {})

    dfu.exitDFUMode(nCard)

    request = json.loads(port.write.call_args.args[0])
    assert request["req"] == "hub.set"
    assert request["mode"] == "dfu-completed"

def test_enterDFUMode():
    nCard, port = createNotecardAndPort()
    setResponse(port, {})

    dfu.enterDFUMode(nCard)

    calls = port.write.call_args_list

    req1 = json.loads(calls[2][0][0])
    assert req1["req"] == "hub.set"
    assert req1["mode"] == "dfu"


    req2 = json.loads(calls[3][0][0])
    assert req2["req"] == "dfu.get"
    

def test_enterDFUMode_fails_on_timeout():
    d = dfu
    nCard, port = createNotecardAndPort()
    m = Mock()
    m.side_effect = [0, 0, 5]
    d.setTimeFunc(m)

    setResponseList(port, [{},{"err":"abc"},{}])

    with pytest.raises(Exception, match="Notecard failed to enter DFU mode"):
        d.enterDFUMode(nCard,timeout_sec=0.001)

    d.resetTimeFunc()



def test_getFileChunk():
    nCard, port = createNotecardAndPort()
    content = b'here is my chunk content'
    payload = str(base64.b64encode(content), 'utf8')
    md5 = hashlib.md5(content).hexdigest()

    setResponse(port, {"payload":payload,"status":md5})

    c = dfu.getFileChunk(nCard, length=4096, offset=0)

    assert c == content

def test_getFileChunk_recovers_from_io_error():
    nCard, port = createNotecardAndPort()
    content = b'here is my chunk content'
    payload = str(base64.b64encode(content), 'utf8')
    md5 = hashlib.md5(content).hexdigest()

    setResponseList(port, [{"err":"\{io\}"},{"payload":payload,"status":md5}])

    c = dfu.getFileChunk(nCard, length=4096, offset=0)

    assert c == content

def test_getFileChunk_too_many_io_error_raises_exception():
    nCard, port = createNotecardAndPort()
    setResponse(port, {"err":"\{io\}"})
    offset = 0
    length = 4096

    message = "Failed to get file chunk at {offset} with length {length}"
    with pytest.raises(Exception, match=message):
        c = dfu.getFileChunk(nCard, length=length, offset=offset)

def test_getFileChunk_no_payload_raises_exception():
    nCard, port = createNotecardAndPort()
    setResponse(port, {})
    offset = 0
    length = 4096

    message = "No content available file chunk at {offset} with length {length}"
    with pytest.raises(Exception, match=message):
        c = dfu.getFileChunk(nCard, length=length, offset=offset)

def test_getFileChunk_md5_mismatch_on_all_retries_raises_exception():
    nCard, port = createNotecardAndPort()
    content = b'here is my chunk content'
    payload = str(base64.b64encode(content), 'utf8')
    md5 = "abc"
    setResponse(port, {"payload":payload,"status":md5})
    offset = 0
    length = 4096

    message = "Failed to get file chunk at {offset} with length {length}"
    with pytest.raises(Exception, match=message):
        c = dfu.getFileChunk(nCard, length=length, offset=offset)


class memStore:
    store = ""
    def write(self, content):
        self.store += content.encode("utf-8")

def test_storeFileContent():
    
    s = memStore()
    nCard, port = createNotecardAndPort()
    content = b'here is my chunk content'
    payload = str(base64.b64encode(content), 'utf8')
    md5 = hashlib.md5(content).hexdigest()

    {
        "mode": "ready",
        "body": {
            "length": len(content),
            "md5": md5,
            "name": name,
            "source": source,
            "version": version,
        }
        }

    setResponseList(port, {"payload":payload,"status":md5})

    dfu.storeFileContent(nCard, writeFn=s.write)

    assert s.store == content
    






