
import os
import sys
import notecard
import json
import pytest
import hashlib
import base64
import io

sys.path.append("src")

import dfu


from contextlib import AbstractContextManager
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
        response = [response, ]

    s = []
    for r in response:
        s.append(convertToSerialStr(r))

    port.readline.side_effect = s

def createReaderWithMockNotecard(card = Mock()):
    return dfu.dfuReader(card, info={"length":7})


def createReaderAndPort():
    nCard, port = createNotecardAndPort()
    r = dfu.dfuReader(nCard, info={"length":7})
    return (r, port)


def addWriteableBytesBuffer(port):
    def writeToBuffer(p, d):
        p.writebuffer += (d)
        return len(d)

    port.writebuffer = b''
    port.write = lambda d: writeToBuffer(port, d)

    return port


def extractRequestsWrittenToBuffer(port):
    reqListInBytes = port.writebuffer.splitlines()
    reqList = []
    for r in reqListInBytes:
        reqList.append(json.loads(r))

    return reqList


def generateBinaryPayloadReader(c):
    b = io.BytesIO(c)
    def f(card, o,s,num_retries=0):
        b.seek(o)
        return b.read(s)
    return f


def createReaderWithBinaryContent(c):
    nCard = Mock()
    
    
    r = dfu.dfuReader(nCard, info={"length":0})
    if c == None:
        r._requestDfuChunk = Mock(return_value=None)
        return r

    b = io.BytesIO(c)

    def f(o, s, num_retries=0):
        b.seek(o)
        return b.read(s)
    r._length = len(c)

    r._requestDfuChunk = Mock(side_effect=f)

    return r


def createReaderWithMockTimersAndPort():
    r, port = createReaderAndPort()
    timerFn = Mock()
    sleepFn = Mock()
    r._getTimeSec = timerFn
    r._sleep = sleepFn

    return (r, port)


def test_dfuReader_constructor_with_known_image_info():
    nCard = Mock()
    info = {"length":7, "md5": 11}
    r = dfu.dfuReader(nCard, info=info)

    assert isinstance(r, AbstractContextManager)
    assert(r.NCard == nCard)
    assert(r._length == info["length"])
    assert(r._imageHash == info["md5"])
    assert(r._offset == 0)
    assert isinstance(r._md5, hashlib._hashlib.HASH)
    assert isinstance(r._watchDog, dfu.emptyDFUWatchDog)


@patch("dfu.getUpdateInfo")
def test_dfuReader_constructor_without_image_info(mock_getInfo):

    nCard = Mock()
    info = {"length":7, "md5": 11}
    mock_getInfo.return_value = info
    r = dfu.dfuReader(nCard)

    assert isinstance(r, AbstractContextManager)
    assert(r.NCard == nCard)
    assert(r._length == info["length"])
    assert(r._imageHash == info["md5"])
    assert(r._offset == 0)
    assert isinstance(r._md5, hashlib._hashlib.HASH)

    mock_getInfo.assert_called_once_with(nCard)

def test_dfuReader_reset_seeks_beginning_of_image_and_restarts_hash():
    nCard = MagicMock()
    r = dfu.dfuReader(nCard, info={"length":11})

    r._offset = 7
    m = r._md5

    r.reset()

    assert r._offset == 0
    assert r._md5 != m



    
# def test_dfuReader_Open_failsToEstablishDfuMode_ClosesDfuMode():
#     d = dfu.dfuReader(Mock())
#     d._requestDfuModeEntry = Mock()
#     f = Mock(return_value=False)
#     d._waitForDfuMode = f
#     d._requestDfuModeExit = Mock()

#     with pytest.raises(Exception):
#         d.Open()

#     d._requestDfuModeExit.assert_called_once()
        


def test_dfuReader__enter__returns_self():
    r = createReaderWithMockNotecard()
    y = r.__enter__()

    assert y == r



@patch("dfu.exitDFUMode")
def test_dfuReader__exit__RequestsDfuModeExit(mock_exitMode):
    r = createReaderWithMockNotecard()
    
    r.__exit__(None, None, None)

    mock_exitMode.assert_called_once_with(r.NCard)
           

@patch("dfu.exitDFUMode")
def test_dfuReader_Close_RequestsDfuModeExit(mock_exitMode):
    r = createReaderWithMockNotecard()
    
    r.close()

    mock_exitMode.assert_called_once()


def test_dfuReader_Readable_True():
    d = createReaderWithMockNotecard()
    assert d.readable() == True


def test_dfuReader_Writable_False():
    d = createReaderWithMockNotecard()
    assert d.writable() == False


def test_dfuReader_Seek_updatesOffsetProp():
    d = createReaderWithMockNotecard()
    assert d._offset == 0
    n = 17
    d.seek(n)
    assert d._offset == n




@patch("dfu._requestDfuChunk")
def test_dfuReader_Read_UpdatesOffsetByLengthOfReadContent(mock_dfuChunk):
    content = b'here is my chunk content'
    mock_dfuChunk.side_effect = generateBinaryPayloadReader(content)
    

    size = len(content)

    r = dfu.dfuReader(MagicMock(), info={"length": size})
    assert r._offset == 0

    c = r.read(size = size+1)

    assert r._offset == size


def test_dfuReader_Read_offsetPointerBeyondContentLength():
    d = createReaderWithMockNotecard()
    

    d._length = 17
    d._offset = 18

    c = d.read()

    assert c == None

@patch("dfu._requestDfuChunk")
def test_dfuReader_Read_sizeBeyondContentLength(mock_dfuChunk):
    mock_dfuChunk.side_effect = generateBinaryPayloadReader(b'aaaaabbbbbbcccccccccccccccccccccccccccccccccc')

    r = dfu.dfuReader(MagicMock(), info={"length":11})
    r._offset = 5
    size = 31

    assert r._offset + size >= r._length
    c = r.read(size=size)

    assert c == b"bbbbbb"

@patch("dfu._requestDfuChunk")
def test_dfuReader_Read_MultipleTimes_readsSubsequentChunks(mock_dfuChunk):
    
    payload1 = b'chunk 1'
    payload2 = b'chunk 2'
    payload = payload1 + payload2
    mock_dfuChunk.side_effect = generateBinaryPayloadReader(payload)
    
    r = dfu.dfuReader(MagicMock(), info={"length":len(payload) + 1})
    

    size1 = len(payload1)
    size2 = len(payload2)

    c = r.read(size = size1)
    assert c == payload1

    c = r.read(size = size2)
    assert c == payload2



@patch("dfu._requestDfuChunk")
def test_dfuReader_Read_UpdatesMd5(mock_dfuChunk):
    payload1 = b'chunk 1'
    payload2 = b'chunk 2'
    payload = payload1 + payload2

    h = hashlib.md5(payload).hexdigest()

    mock_dfuChunk.side_effect = generateBinaryPayloadReader(payload)

    r = dfu.dfuReader(MagicMock(), info={"length":len(payload)})
    
    size1 = len(payload1)
    size2 = len(payload2)

    r.read(size=size1)
    r.read(size=size2)

    assert r._md5.hexdigest() == h

def test_dfuReader_Read_watchDogNotPatIfNoRead():

    w = MagicMock()
    r = dfu.dfuReader(MagicMock(), info={"length":1})
    r._watchDog = w

    r.read(size=0)

    w.pat.assert_not_called()

@patch("dfu._requestDfuChunk")
def test_dfuReader_Read_watchDogPatIfReadAttempted(mock_dfuChunk):

    payload = b'random payload'
    mock_dfuChunk.side_effect = generateBinaryPayloadReader(payload)

    w = MagicMock()
    r = dfu.dfuReader(MagicMock(), info={"length":len(payload)})
    r._watchDog = w

    r.read()

    w.pat.call_once_with()




def test_dfuReader_GetHash():
    d = createReaderWithMockNotecard()
    m = d._md5

    h = d.get_hash()

    assert h == m.hexdigest()






def test_dfuReader_CheckHash():
    d = createReaderWithMockNotecard()
    d._imageHash = 'abcd'
    d.get_hash = Mock(return_value='abcd')

    assert d.check_hash()

    d.get_hash = Mock(return_value='def')

    assert not d.check_hash()


def test_requestDfuChunk_no_payload_raises_exception():
    card, port = createNotecardAndPort()
    setResponse(port, {})
    message = f"No content available at 0 with length 4096"
    with pytest.raises(Exception, match=message):
        c = dfu._requestDfuChunk(card, 0, 4096)


def test_dfuReader_Read_failureDoesNotUpdateReaderOffset():
    d = createReaderWithMockNotecard()
    n = 17
    d._offset = n
    d._requestDfuChunk = Mock(side_effect=Exception("request failed"))

    assert d._offset == n


def test_dfuReader_Read_tooManyFailedReadsRaisesException():
    nc = Mock()
    nc.Transaction.return_value = {"err": "error message"}
    d = createReaderWithMockNotecard(nc)

    d._length = 1

    num_retries = 2
    message = f"Failed to read content after {num_retries} retries"
    with pytest.raises(Exception, match=message):
        c = d.read(num_retries=num_retries)

    assert d._offset == 0
    assert nc.Transaction.call_count == num_retries


def test_dfuReader_Read_chunkReadFails_RaisesException():
    nc = Mock()
    nc.Transaction.return_value = {"err": "error message"}
    d = createReaderWithMockNotecard(nc)

    d._length = 1

    num_retries = 2
    message = f"Failed to read content after {num_retries} retries"
    with pytest.raises(Exception, match=message):
        c = d.read(num_retries=num_retries)
    assert d._offset == 0
    assert nc.Transaction.call_count == num_retries


def test_dfuReader_useWatchdog_appliesWatchdogIfProvided():
    
    r = dfu.dfuReader(MagicMock(), info={"length":0})

    w = MagicMock()

    r.useWatchdog(w)

    assert r._watchDog == w


def test_dfuReader_useWatchdog_appliesDFUWatchDogIfNoArgumentProvided():
    
    r = dfu.dfuReader(MagicMock(), info={"length":0})

    w = MagicMock()

    r.useWatchdog()

    assert isinstance(r._watchDog, dfu.dfuWatchDog)



def test_requestDfuChunk_md5Mismatch_raisesException():
    card, port = createNotecardAndPort()
    content = b'here is my chunk content'
    payload = str(base64.b64encode(content), 'utf8')
    md5 = "abc"
    setResponse(port, {"payload": payload, "status": md5})

    with pytest.raises(Exception, match="content checksum mismatch"):
        c = dfu._requestDfuChunk(card, 0, 1)
    


def test_requestDfuChunk_notecardErrResponse_raisesException():
    card, port = createNotecardAndPort()
    m = "notecard had an error"
    setResponse(port, {"err": m})

    with pytest.raises(Exception, match=m):
        c = dfu._requestDfuChunk(card, 0, 1)


def test_requestDfuChunk_returnsContent():
    card, port = createNotecardAndPort()
    content = b'here is my chunk content'
    payload = str(base64.b64encode(content), 'utf8')
    md5 = hashlib.md5(content).hexdigest()
    setResponse(port, {"payload":payload,"status":md5})
    
    c = dfu._requestDfuChunk(card, 0, len(payload))
    assert c == content

@patch("dfu._requestDfuChunk")
def test_dfuReader_ReadToWriter_CopiesReadContentToWriter(mock_dfuChunk):
    content = b'here is my chunk content'
    mock_dfuChunk.side_effect = generateBinaryPayloadReader(content)

    w = io.BytesIO(b"")

    r = dfu.dfuReader(MagicMock(), info={"length":len(content)})
    s = r.read_to_writer(w)

    assert s == len(content)
    assert w.getvalue() == content

@patch("dfu._requestDfuChunk")
def test_dfuReader_ReadToWriter_ReturnsNumBytesWritten(mock_dfuChunk):
    mock_dfuChunk.side_effect = generateBinaryPayloadReader(b'a')

    r = dfu.dfuReader(MagicMock(), info={"length":1})

    n = 1
    w = Mock()
    w.write.return_value = n

    s = r.read_to_writer(w)

    assert s == n


def test_dfuReader_ReadToWriter_tooManyFailedReadsRaisesException():
    nc = Mock()
    nc.Transaction.return_value = {"err": "error message"}
    d = createReaderWithMockNotecard(nc)
    
    
    w = Mock()
    d._length = 1

    num_retries = 2
    message = f"Failed to read content after {num_retries} retries"
    with pytest.raises(Exception, match=message):
        c = d.read_to_writer(w, num_retries=num_retries)

    assert d._offset == 0
    assert nc.Transaction.call_count == num_retries


@patch("dfu._requestDfuChunk")
def test_dfuReader_ReadToWriter_MultipleTimes_writesSubsequentChunks(mock_dfuChunk):
    
    payload1 = b'chunk 1'
    payload2 = b'chunk 2'
    mock_dfuChunk.side_effect = generateBinaryPayloadReader(payload1+payload2)
    

    size1 = len(payload1)
    size2 = len(payload2)

    r = dfu.dfuReader(MagicMock(), info={"length":size1+size2})
    
    w = Mock()
    w.write.side_effect = [size1, size2]

    c = r.read_to_writer(w, size = size1)
    assert payload1 in w.write.call_args[0]

    c = r.read_to_writer(w, size = size2)
    assert payload2 in w.write.call_args[0]


def test_dfuReader_GetInfo():

    d, port = createReaderAndPort()
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

    f = d.GetInfo()

    assert f["length"] == fileLength
    assert f["crc32"] == crc32
    assert f["md5"] == md5
    assert f["name"] == name
    assert f["source"] == source


def test_isUpdateAvailable_when_file_available():
    nCard, port = createNotecardAndPort()

    setResponse(port, {
        "mode": "ready",
        "status": "successfully downloaded",
    })

    tf = dfu.isUpdateAvailable(nCard)

    assert tf == True


def test_isUpdateAvailable_when_not_available():

    nCard, port = createNotecardAndPort()

    setResponse(port, {"mode": "idle"})

    tf = dfu.isUpdateAvailable(nCard)

    assert tf == False

    setResponse(port, {"mode": "downloading"})

    tf = dfu.isUpdateAvailable(nCard)

    assert tf == False

    setResponse(port, {"mode": "error"})

    tf = dfu.isUpdateAvailable(nCard)

    assert tf == False


def test_isUpdateAvailable_response_has_error():

    nCard, port = createNotecardAndPort()

    message = "something went wrong"
    setResponse(port, {
        "err": message
    })

    with pytest.raises(Exception, match="Notecard returned error: " + message):
        f = dfu.isUpdateAvailable(nCard)


def test_getUpdateInfo_when_file_available():

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

    f = dfu.getUpdateInfo(nCard)

    assert f["length"] == fileLength
    assert f["crc32"] == crc32
    assert f["md5"] == md5
    assert f["name"] == name
    assert f["source"] == source


def test_getUpdateInfo_response_has_error():

    nCard, port = createNotecardAndPort()

    message = "something went wrong"
    setResponse(port, {
        "err": message
    })

    with pytest.raises(Exception, match="Notecard returned error: " + message):
        f = dfu.getUpdateInfo(nCard)


def test_getUpdateInfo_when_not_available():

    nCard, port = createNotecardAndPort()

    setResponse(port, {"mode": "idle"})

    f = dfu.getUpdateInfo(nCard)

    assert f == None

    setResponse(port, {"mode": "downloading"})

    f = dfu.getUpdateInfo(nCard)

    assert f == None

    setResponse(port, {"mode": "error"})

    f = dfu.getUpdateInfo(nCard)

    assert f == None

    setResponse(port, {"random-field":   "random-value"})

    f = dfu.getUpdateInfo(nCard)

    assert f == None

def test_enterDFUMode_sendsRequestToNotecard():
    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)

    setResponse(port, {})
    dfu.enterDFUMode(nCard)

    req1 = json.loads(port.writebuffer)
    assert req1["req"] == "hub.set"
    assert req1["mode"] == "dfu"

def test_enterDFUMode_notecardReturnsErr_raiseException():
    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)

    setResponse(port, {"err":"some error message"})
    
    

    with pytest.raises(Exception, match="Notecard request for DFU mode entry failed"):
        dfu.enterDFUMode(nCard)


def test_exitDFUMode_sendsRequestToNotecard():
    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)

    setResponse(port, {})
    dfu.exitDFUMode(nCard)

    req1 = json.loads(port.writebuffer)
    assert req1["req"] == "hub.set"
    assert req1["mode"] == "dfu-completed"

def test_exitDFUMode_notecardReturnsErr_raiseException():
    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)

    setResponse(port, {"err":"some error message"})

    with pytest.raises(Exception, match="Notecard request for DFU mode exit failed"):
        dfu.exitDFUMode(nCard)

def test_setUpdateDone_providesStatusToNotecard():
    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)
    setResponse(port, {})
    message = "mark completed"

    dfu.setUpdateDone(nCard, message)

    reqList = extractRequestsWrittenToBuffer(port)

    req1 = reqList[0]
    assert req1["req"] == "dfu.status"
    assert req1["stop"] == True
    assert req1["status"] == message


def test_setUpdateDone_transationFailsRaisesException():
    nCard, port = createNotecardAndPort()

    message = "something went wrong"
    setResponse(port, {
        "err": message
    })

    with pytest.raises(Exception, match="Notecard returned error: " + message):
        dfu.setUpdateDone(nCard, "")


def test_setUpdateError_providesStatusToNotecard():
    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)

    setResponse(port, {})
    message = "mark failure"

    dfu.setUpdateError(nCard, message)

    reqList = extractRequestsWrittenToBuffer(port)

    req1 = reqList[0]
    assert req1["req"] == "dfu.status"
    assert req1["stop"] == True
    assert req1["err"] == message
    # required for older versions of Notecard firmware
    assert req1["status"] == message


def test_enableUpdate_sendsRequestToNotecard():
    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)
    setResponse(port, {})

    dfu.enableUpdate(nCard)

    req1 = extractRequestsWrittenToBuffer(port)[0]
    assert req1["req"] == "dfu.status"
    assert req1["on"] == True


def test_enableUpdate_NotecardReturnsErrorRaiseException():
    nCard, port = createNotecardAndPort()
    message = "something went wrong"
    setResponse(port, {
        "err": message
    })

    with pytest.raises(Exception, match="Notecard returned error: " + message):
        dfu.enableUpdate(nCard)


def test_disableUpdate_sendsRequestToNotecard():
    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)
    setResponse(port, {})

    dfu.disableUpdate(nCard)

    req1 = extractRequestsWrittenToBuffer(port)[0]
    assert req1["req"] == "dfu.status"
    assert req1["off"] == True


def test_disableUpdate_NotecardReturnsErrorRaiseException():
    nCard, port = createNotecardAndPort()
    message = "something went wrong"
    setResponse(port, {
        "err": message
    })

    with pytest.raises(Exception, match="Notecard returned error: " + message):
        dfu.disableUpdate(nCard)


# @patch("dfu.enterDFUMode")
# def test_open_requestsDfuStatus(mock_enter):
    

#     nCard, port = createNotecardAndPort()
#     port = addWriteableBytesBuffer(port)

#     setResponse(port, {})
#     dfu.open(nCard)

#     req1 = json.loads(port.writebuffer)
#     assert req1["req"] == "hub.set"
#     assert req1["mode"] == "dfu"


def test_isDFUModeActive_sendsRequestToNotecard():
    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)

    setResponse(port, {})

    dfu.isDFUModeActive(nCard)

    req1 = json.loads(port.writebuffer)
    assert req1["req"] == "dfu.get"

def test_isDFUModeActive_returnsFalseIfErrInResponse():
    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)

    setResponse(port, {"err":"has an error"})

    success = dfu.isDFUModeActive(nCard)

    assert not success


def test_isDFUModeActive_returnsTrueIfNoErrInResponse():
    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)

    setResponse(port, {})

    success = dfu.isDFUModeActive(nCard)

    assert success

@patch("dfu.isDFUModeActive")
def test_waitForDFUMode_returnsIfInDFUMode(mock_isactive):
    mock_isactive.return_value = True

    nCard, port = createNotecardAndPort()
    dfu.waitForDFUMode(nCard)


@patch("dfu.isDFUModeActive")
def test_waitForDFUMode_raisesExceptionOnTimeout(mock_isactive):
    mock_isactive.return_value = False

    nCard, port = createNotecardAndPort()
    t = MagicMock()
    t.side_effect = [0, 8]
    
    with pytest.raises(Exception, match="timed out"):
        dfu.waitForDFUMode(nCard, timeoutMS = 7, getTimeMS = t, sleepMS = MagicMock())


@patch("dfu.isDFUModeActive")
def test_waitForDFUMode_calls_sleep_function(mock_isactive):
    mock_isactive.side_effect = [False, True]

    nCard, port = createNotecardAndPort()
    t = MagicMock()
    t.return_value = 0

    s = MagicMock()
    sleepPeriod = 7
    
    dfu.waitForDFUMode(nCard, retryPeriodMS = sleepPeriod, getTimeMS = t, sleepMS = s)

    s.assert_called_once_with(sleepPeriod)

@patch("dfu.sleep")
@patch("dfu.isDFUModeActive")
def test_waitForDFUMode_calls_default_sleep_function(mock_isactive, mock_sleep):
    mock_isactive.side_effect = [False, True]

    nCard, port = createNotecardAndPort()
    t = MagicMock()
    t.return_value = 0

    sleepPeriodSec = 7
    
    dfu.waitForDFUMode(nCard, retryPeriodMS = sleepPeriodSec*1000, getTimeMS = t)

    mock_sleep.assert_called_once_with(sleepPeriodSec)





@patch("dfu.isDFUModeActive")
@patch("dfu.getUpdateInfo")
def test_open_requestsDfuMode(mock_getInfo, mock_isactive):
    mock_isactive.return_value = True
    mock_getInfo.return_value = {"length": 7}

    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)

    setResponse(port, {})
    dfu.open(nCard)

    req1 = json.loads(port.writebuffer)
    assert req1["req"] == "hub.set"
    assert req1["mode"] == "dfu"



@patch("dfu.isDFUModeActive")
@patch("dfu.getUpdateInfo")
def test_open_returnsDFUReader(mock_getInfo, mock_isactive):
    mock_getInfo.return_value = {"length":0}
    mock_isactive.return_value = True

    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)

    setResponse(port, {})
    r = dfu.open(nCard)

    assert isinstance(r, dfu.dfuReader)
    assert isinstance(r, AbstractContextManager)

    

@patch("dfu._requestDfuChunk")
@patch("dfu.open")
def test_copyImageToWriter_populatesWriterWithContent(mock_open, mock_dfuChunk):

    payload = b'chunk 1'
    mock_dfuChunk.side_effect = generateBinaryPayloadReader(payload)

    
    r = dfu.dfuReader(MagicMock(), info={"length":len(payload), "md5":hashlib.md5(payload).hexdigest()})

    mock_open.return_value = r

    writer = MagicMock()
    writer.write.return_value = len(payload)

    dfu.copyImageToWriter(MagicMock(), writer)

    writer.write.assert_called_once_with(payload)

def test_dfuReader_readToWriter_readsNoContent():
    nCard, port = createNotecardAndPort()
    reader = dfu.dfuReader(nCard, info={"length":0})

    writer = Mock()

    n = reader.read_to_writer(writer)

    assert n == 0
    assert writer.write.call_count == 0

@patch("dfu.open")
def test_copyImageToWriter_throwsErr_closesDfu(mock_open):
    r = dfu.dfuReader(MagicMock(), info={"length":0})
    r.read_to_writer = MagicMock(side_effect = Exception("error occurred"))
    r.close = MagicMock()

    mock_open.return_value = r
    writer = MagicMock()

    with pytest.raises(Exception, match="error occurred"):
        dfu.copyImageToWriter(MagicMock(), writer)

    r.read_to_writer.assert_called()
    r.close.assert_called()


@patch("dfu.open")
def test_copyImageToWriter_throwsErrOnHashMismatch(mock_open):
    r = dfu.dfuReader(MagicMock(), info={"length":1})
    r.read_to_writer = MagicMock(return_value=0)
    r.check_hash = MagicMock(return_value = False)
    r.close = MagicMock()
    mock_open.return_value = r

    writer = Mock()

    with pytest.raises(Exception, match="Image hash mismatch"):
        dfu.copyImageToWriter(MagicMock(), writer)

    r.read_to_writer.assert_called()
    r.close.assert_called()

@patch("dfu.open")
def test_copyImageToWriter_callsProgressUpdaterWithPercentCompletion(mock_open):
    totalLength = 4
    readLength = 1
    r = dfu.dfuReader(MagicMock(), info={"length":totalLength})
    r.read = MagicMock(return_value=b'a')
    r.check_hash = MagicMock(return_value=True)
    mock_open.return_value = r
    writer = MagicMock()
    writer.write.side_effect = [readLength, 0]

    
    progressUpdater = MagicMock()

    dfu.copyImageToWriter(MagicMock(), writer, size=readLength, progressUpdater=progressUpdater)

    progressUpdater.assert_called_with(int((readLength) * 100 / totalLength))



@patch("dfu.open")
@patch("dfu.isWatchdogRequired")
def test_copyImageToWriter_applysWatchDogIfRequired(mock_isRequired, mock_open):
    mock_isRequired.return_value = True

    totalLength = 4
    readLength = 1
    r = dfu.dfuReader(MagicMock(), info={"length":totalLength})
    r.read = MagicMock(return_value=b'a')
    r.check_hash = MagicMock(return_value=True)
    r.useWatchdog = MagicMock()
    mock_open.return_value = r
    writer = MagicMock()
    writer.write.side_effect = [readLength, 0]


    card = MagicMock()
    dfu.copyImageToWriter(card, writer, size=readLength, suppressWatchdog = False)

    mock_isRequired.assert_called_once_with(card)
    r.useWatchdog.assert_called_once_with()


@patch("dfu.open")
@patch("dfu.isWatchdogRequired")
def test_copyImageToWriter_doesNotApplysWatchDogIfNotRequired(mock_isRequired, mock_open):
    mock_isRequired.return_value = False

    totalLength = 4
    readLength = 1
    r = dfu.dfuReader(MagicMock(), info={"length":totalLength})
    r.read = MagicMock(return_value=b'a')
    r.check_hash = MagicMock(return_value=True)
    r.useWatchdog = MagicMock()
    mock_open.return_value = r
    writer = MagicMock()
    writer.write.side_effect = [readLength, 0]


    card = MagicMock()
    dfu.copyImageToWriter(card, writer, size=readLength, suppressWatchdog = False)

    mock_isRequired.assert_called_once_with(card)
    r.useWatchdog.assert_not_called()

def test_setVersion_SendsNotecardRequest():
    nCard, port = createNotecardAndPort()
    port = addWriteableBytesBuffer(port)

    setResponse(port, {})
    verString = "2.5.7.11"

    dfu.setVersion(nCard, verString)

    req1 = extractRequestsWrittenToBuffer(port)[0]
    assert req1["req"] == "dfu.status"
    assert req1["version"] == verString


def test_emptyDFUWatchDog_instantiates_and_does_nothing_on_pat():
    card = MagicMock()
    d = dfu.emptyDFUWatchDog(card)
    d.pat()

    card.Transaction.assert_not_called()


def test_dfuWatchDog_constructor_setsInstanceProperties():
    card = MagicMock()

    d = dfu.dfuWatchDog(card)

    assert d.card == card
    assert d._timeout == 0

    d = dfu.dfuWatchDog(card, periodMS = 17)
    assert d._periodMS == 17

    g = MagicMock()
    d = dfu.dfuWatchDog(card, getTimeMS=g)
    assert d._getTimeMS == g




def test_dfuWatchDog_pat_timerNotExpired_doesNotSendMessageToNotecard():
    card = MagicMock()

    getTimeMS = MagicMock(return_value=13)
    d = dfu.dfuWatchDog(card, getTimeMS = getTimeMS)
    d._timeout = 17

    d.pat()

    card.Transaction.assert_not_called()


def test_dfuWatchDog_pat_timerExpired_sendsRequestToNotecard_resetsTimeout():
    card = MagicMock()

    n = 17
    p = 19
    getTimeMS = MagicMock(return_value=n)
    d = dfu.dfuWatchDog(card, periodMS = p, getTimeMS=getTimeMS)

    d.pat()

    
    card.Transaction.assert_called_once_with({"req":"hub.set","mode":"dfu"})
    
    getTimeMS.assert_called_once()

    assert d._timeout == n+p

def test_isWatchdogRequired():
    card = MagicMock()

    def setVersion(major, minor, patch, build=0):

        card.version.return_value = {"body":{
            "version":f"notecard-{major}.{minor}.{patch}",
            "ver_major": major,
            "ver_minor": minor,
            "ver_patch": patch,
            "ver_build": build
        },
        "api": 1
        }
    
    
    setVersion(1,5,1)
    assert dfu.isWatchdogRequired(card) == True
    
    setVersion(2,1,1)
    assert dfu.isWatchdogRequired(card) == True

    
    setVersion(3,1,1)
    assert dfu.isWatchdogRequired(card) == True

    setVersion(3,2,1)
    assert dfu.isWatchdogRequired(card) == True

    setVersion(2,3,1)
    assert dfu.isWatchdogRequired(card) == False

    
    setVersion(3,3,1)
    assert dfu.isWatchdogRequired(card) == False


    setVersion(2,4,1)
    assert dfu.isWatchdogRequired(card) == False

    
    setVersion(3,4,1)
    assert dfu.isWatchdogRequired(card) == False



