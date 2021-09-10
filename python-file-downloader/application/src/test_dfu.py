
import os
import sys
import notecard
import json
import pytest
import hashlib
import base64
import io

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


def createReaderWithMockNotecard(card = Mock()):
    return dfu.dfuReader(card)


def createReaderAndPort():
    nCard, port = createNotecardAndPort()
    r = dfu.dfuReader(nCard)
    return (r, port)

def createReaderWithBinaryContent(c):
    nCard = Mock()
    
    
    r = dfu.dfuReader(nCard)
    if c == None:
        r._requestDfuChunk = Mock(return_value=None)
        return r
    
    b = io.BytesIO(c)
    def f(o,s,num_retries=0):
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


def test_dfuReader():
    nCard = Mock()
    d = dfu.dfuReader(nCard)

    assert(d.NCard == nCard)
    assert(d.OpenTimeoutSec == 120)

def test_dfuReader_privateProperties():
    nCard = Mock()
    d = dfu.dfuReader(nCard)

    assert d._length == 0
    assert d._offset == 0
    assert d._imageHash == None
    assert type(d._md5).__name__ == 'HASH'





def test_dfuReader_Open_requestsDfuModeAndWaits():
    d = dfu.dfuReader(Mock())
    e = Mock()
    w = Mock()
    d._requestDfuModeEntry = e
    d._waitForDfuMode = w
    d.GetInfo = Mock(return_value = {"length":0})
    d.Open()

    e.assert_called_once()
    w.assert_called_once()

def test_dfuReader_requestDfuModeEntry_sendsRequestToNotecard():
    d, port = createReaderAndPort()
    setResponse(port, {})
    d._requestDfuModeEntry()

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
    d.GetInfo = Mock(return_value = {"length":0})
    

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
    d = dfu.dfuReader(Mock())
    d._requestDfuModeEntry = Mock()
    f = Mock(return_value=False)
    d._waitForDfuMode = f
    d._requestDfuModeExit = Mock()

    with pytest.raises(Exception):
        d.Open()

    d._requestDfuModeExit.assert_called_once()
        
def test_dfuReader_Open_setsOffsetToBeginning():
    d = createReaderWithMockNotecard()
    d._requestDfuModeEntry = Mock()
    d._waitForDfuMode = Mock(return_value=True)
    d.GetInfo = Mock(return_value = {"length":0})
    d._offset = 1

    d.Open()

    assert d._offset == 0

def test_dfuReader_Open_setsReaderLengthProp():
    d = createReaderWithMockNotecard()
    assert d._length == 0
    length = 17
    d._requestDfuModeEntry = Mock()
    d._waitForDfuMode = Mock(return_value=True)
    d.GetInfo = Mock(return_value={"length":length})
    
    d.Open()

    assert d._length == length

            

def test_dfuReader_requestDfuModeExit_callsNotecard():
    d, port = createReaderAndPort()
    setResponse(port, {})

    d._requestDfuModeExit()

    calls = port.write.call_args_list
    req1 = json.loads(calls[2][0][0])
    assert req1["req"] == "hub.set"
    assert req1["mode"] == "dfu-completed"


def test_dfuReader_requestDfuModeExit_callsNotecard_failureRaisesException():
    d, port = createReaderAndPort()
    setResponse(port, {"err":"some error message"})

    with pytest.raises(Exception, match="Notecard request for DFU mode exit failed"):
        d._requestDfuModeExit()


def test_dfuReader_Close_RequestsDfuModeExit():
    d = createReaderWithMockNotecard()
    d._requestDfuModeExit = Mock()

    d.Close()

    d._requestDfuModeExit.assert_called_once()


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

def test_dfuReader_Read_UpdatesOffsetByLengthOfReadContent():
    content = b'here is my chunk content'
    d = createReaderWithBinaryContent(content)
    size = len(content)

    assert d._offset == 0

    c = d.read(size = size+1)

    assert d._offset == size

def test_dfuReader_Read_offsetPointerBeyondContentLength():
    d = createReaderWithMockNotecard()
    d._length = 17
    d._offset = 18

    c = d.read()

    assert c == None


def test_dfuReader_Read_sizeBeyondContentLength():
    d = createReaderWithBinaryContent(b'aaaaabbbbbbcccccccccccccccccccccccccccccccccc')
    d._length = 11
    d._offset = 5
    size = 31

    assert d._offset + size >= d._length
    c = d.read(size=size)

    assert c == b"bbbbbb"

def test_dfuReader_Read_MultipleTimes_readsSubsequentChunks():
    
    payload1 = b'chunk 1'
    payload2 = b'chunk 2'
    d = createReaderWithBinaryContent(payload1+payload2)
    size1 = len(payload1)
    size2 = len(payload2)
    
    w = Mock()
    w.write.side_effect = [size1, size2]

    c = d.read(size = size1)
    assert c == payload1

    c = d.read(size = size2)
    assert c == payload2


def test_dfuReader_Read_UpdatesMd5():
    payload1 = b'chunk 1'
    payload2 = b'chunk 2'
    payload = payload1 + payload2
    d = createReaderWithBinaryContent(payload)
    d.reset_hash()
    
    size1 = len(payload1)
    size2 = len(payload2)

    d.read(size=size1)
    d.read(size=size2)

    assert d._md5.hexdigest() == hashlib.md5(payload).hexdigest()


def test_dfuReader_ResetHash():
    d = createReaderWithMockNotecard()
    m = d._md5

    d.reset_hash()
    assert d._md5 != m

def test_dfuReader_GetHash():
    d = createReaderWithMockNotecard()
    m = d._md5

    h = d.get_hash()

    assert h == m.hexdigest()


def test_dfuReader_Open_ResetsHash():
    d = createReaderWithMockNotecard()
    d._requestDfuModeEntry = Mock()
    d._waitForDfuMode = Mock(return_value=True)
    d.GetInfo = Mock(return_value = {"length":0})

    m = d._md5

    d.Open()

    assert d._md5 != m

def test_dfuReader_Open_StoresDfuImageHash():
    d = createReaderWithMockNotecard()
    d._requestDfuModeEntry = Mock()
    d._waitForDfuMode = Mock(return_value=True)
    md5 = 'abcd'
    d.GetInfo = Mock(return_value = {"length":0,"md5":md5})

    d.Open()

    assert d._imageHash == md5


def test_dfuReader_CheckHash():
    d = createReaderWithMockNotecard()
    d._imageHash = 'abcd'
    d.get_hash = Mock(return_value='abcd')

    assert d.check_hash()

    d.get_hash = Mock(return_value='def')

    assert not d.check_hash()


def test_dfuReader_requestDfuChunk_no_payload_raises_exception():
    d, port = createReaderAndPort()
    setResponse(port, {})
    message = f"No content available at 0 with length 4096"
    with pytest.raises(Exception, match=message):
        c = d._requestDfuChunk(0, 4096)

def test_dfuReader_Read_failureDoesNotUpdateReaderOffset():
    d = createReaderWithMockNotecard()
    n = 17
    d._offset = n
    d._requestDfuChunk = Mock(side_effect=Exception("request failed"))

    assert d._offset == n

def test_dfuReader_Read_tooManyFailedReadsRaisesException():
    nc = Mock()
    nc.Transaction.return_value = {"err":"error message"}
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
    nc.Transaction.return_value = {"err":"error message"}
    d = createReaderWithMockNotecard(nc)
    d._length = 1
    
    num_retries = 2
    message = f"Failed to read content after {num_retries} retries"
    with pytest.raises(Exception, match=message):
        c = d.read(num_retries=num_retries)
    assert d._offset == 0
    assert nc.Transaction.call_count == num_retries


def test_dfuReader_requestDfuChunk_md5Mismatch_raisesException():
    d, port = createReaderAndPort()
    content = b'here is my chunk content'
    payload = str(base64.b64encode(content), 'utf8')
    md5 = "abc"
    setResponse(port, {"payload":payload,"status":md5})

    with pytest.raises(Exception, match="content checksum mismatch"):
        c = d._requestDfuChunk(0, 1)
    


def test_dfuReader_requestDfuChunk_notecardErrResponse_raisesException():
    d, port = createReaderAndPort()
    m = "notecard had an error"
    setResponse(port, {"err":m})
    
    with pytest.raises(Exception, match=m):
        c = d._requestDfuChunk(0, 1)


def test_dfuReader_requestDfuChunk_returnsContent():
    d, port = createReaderAndPort()
    content = b'here is my chunk content'
    payload = str(base64.b64encode(content), 'utf8')
    md5 = hashlib.md5(content).hexdigest()
    setResponse(port, {"payload":payload,"status":md5})
    
    c = d._requestDfuChunk(0, len(payload))
    assert c == content

def test_dfuReader_ReadToWriter_CopiesReadContentToWriter():
    content = b'here is my chunk content'
    d = createReaderWithBinaryContent(content)
    w = io.BytesIO(b"")

    s = d.read_to_writer(w)

    assert s == len(content)
    assert w.getvalue() == content

def test_dfuReader_ReadToWriter_ReturnsNumBytesWritten():
    r = createReaderWithBinaryContent(b'a')
    n = 1
    w = Mock()
    w.write.return_value = n

    s = r.read_to_writer(w)

    assert s == n
    

def test_dfuReader_ReadToWriter_tooManyFailedReadsRaisesException():
    nc = Mock()
    nc.Transaction.return_value = {"err":"error message"}
    d = createReaderWithMockNotecard(nc)
    w = Mock()
    d._length = 1

    num_retries = 2
    message = f"Failed to read content after {num_retries} retries"
    with pytest.raises(Exception, match=message):
        c = d.read_to_writer(w, num_retries=num_retries)
    
    assert d._offset == 0
    assert nc.Transaction.call_count == num_retries
   

def test_dfuReader_ReadToWriter_MultipleTimes_writesSubsequentChunks():
    
    payload1 = b'chunk 1'
    payload2 = b'chunk 2'
    d = createReaderWithBinaryContent(payload1+payload2)
    size1 = len(payload1)
    size2 = len(payload2)
    
    w = Mock()
    w.write.side_effect = [size1, size2]

    c = d.read_to_writer(w, size = size1)
    assert payload1 in w.write.call_args[0]

    c = d.read_to_writer(w, size = size2)
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
        "mode":   "ready",
        "status": "successfully downloaded",
        })

    tf = dfu.isUpdateAvailable(nCard)

    assert tf == True

def test_isUpdateAvailable_when_not_available():

    nCard, port = createNotecardAndPort()

    setResponse(port, {"mode":   "idle"})

    tf = dfu.isUpdateAvailable(nCard)

    assert tf == False

    setResponse(port, {"mode":   "downloading"})

    tf = dfu.isUpdateAvailable(nCard)

    assert tf == False

    setResponse(port, {"mode":   "error"})

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

    setResponse(port, {"mode":   "idle"})

    f = dfu.getUpdateInfo(nCard)

    assert f == None

    setResponse(port, {"mode":   "downloading"})

    f = dfu.getUpdateInfo(nCard)

    assert f == None

    setResponse(port, {"mode":   "error"})

    f = dfu.getUpdateInfo(nCard)

    assert f == None

def test_setUpdateDone_providesStatusToNotecard():
    nCard, port = createNotecardAndPort()
    setResponse(port, {})
    message = "mark completed"

    dfu.setUpdateDone(nCard, message)

    

    calls = port.write.call_args_list
    req1 = json.loads(calls[2][0][0])
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
        dfu.setUpdateDone(nCard,"")



def test_setUpdateError_providesStatusToNotecard():
    nCard, port = createNotecardAndPort()
    setResponse(port, {})
    message = "mark failure"

    dfu.setUpdateError(nCard, message)

    

    calls = port.write.call_args_list
    req1 = json.loads(calls[2][0][0])
    assert req1["req"] == "dfu.status"
    assert req1["stop"] == True
    assert req1["err"] == message
    assert req1["status"] == message # required for older versions of Notecard firmware


def test_enableUpdate_sendsRequestToNotecard():
    nCard, port = createNotecardAndPort()
    setResponse(port, {})
    
    dfu.enableUpdate(nCard)

    calls = port.write.call_args_list
    req1 = json.loads(calls[2][0][0])
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
    setResponse(port, {})
    
    dfu.disableUpdate(nCard)

    calls = port.write.call_args_list
    req1 = json.loads(calls[2][0][0])
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





def test_openDfuForRead():
    nCard, port = createNotecardAndPort()
    setResponse(port, {"mode":"ready","body":{"length":5000}})
    with dfu.openDfuForRead(nCard) as r:
        req = json.loads(port.write.call_args_list[3][0][0])
        assert req["req"] == 'dfu.get'
        assert (r.__class__ is dfu.dfuReader)

    req = json.loads(port.write.call_args_list[5][0][0])
    assert req["mode"] == 'dfu-completed'

def test_openDfuForRead_mockReader():
    nCard, port = createNotecardAndPort()
    reader = Mock()
    with dfu.openDfuForRead(nCard,reader=reader) as r:
        assert r == reader
        assert reader.Open.called_once()

    assert reader.Close.called_once()

def test_openDfuForRead_readerMethodthrowsErr_closesDfu():
    nCard, port = createNotecardAndPort()
    reader = Mock()
    reader.read.side_effect = Exception("error occurred")

    with pytest.raises(Exception, match="error occurred"):
        with dfu.openDfuForRead(nCard, reader=reader) as r:
            r.read()

    reader.read.assert_called()
    reader.Close.assert_called()


def test_copyImageToWriter():
    nCard, port = createNotecardAndPort()
    reader = Mock()
    reader._length = 1
    reader.read_to_writer.side_effect = [1,0]
    writer = Mock()

    dfu.copyImageToWriter(nCard, writer, reader=reader)

    reader.read_to_writer.assert_called()
    reader.Close.assert_called()


def test_dfuReader_readToWriter_readsNoContent():
    nCard, port = createNotecardAndPort()
    reader = dfu.dfuReader(nCard)
    writer = Mock()

    n = reader.read_to_writer(writer)

    assert n == 0
    assert writer.write.call_count == 0

def test_copyImageToWriter_throwsErr_closesDfu():
    nCard, port = createNotecardAndPort()
    reader = Mock()
    reader.read_to_writer.side_effect = Exception("error occurred")
    writer = Mock()

    with pytest.raises(Exception, match="error occurred"):
        dfu.copyImageToWriter(nCard, writer, reader=reader)

    reader.read_to_writer.assert_called()
    reader.Close.assert_called()


def test_copyImageToWriter_throwsErrOnHashMismatch():
    nCard, port = createNotecardAndPort()
    reader = Mock()
    reader._length = 1
    reader.read_to_writer.return_value = 0
    reader.check_hash.return_value = False
    writer = Mock()

    with pytest.raises(Exception, match="Image hash mismatch"):
        dfu.copyImageToWriter(nCard, writer, reader=reader)

    reader.read_to_writer.assert_called()
    reader.Close.assert_called()

def test_copyImageToWriter_callsProgressUpdaterWithPercentCompletion():
    nCard = Mock()
    reader = Mock()
    totalLength = 4
    readLength = 1
    reader.read_to_writer.side_effect = [readLength,readLength,0]
    reader._length = totalLength
    writer = Mock()
    progressUpdater = Mock()

    dfu.copyImageToWriter(nCard, writer, reader=reader,progressUpdater=progressUpdater)

    progressUpdater.assert_called_with(int((readLength + readLength) * 100 / totalLength))
    


def test_setVersion_SendsNotecardRequest():
    nCard, port = createNotecardAndPort()
    setResponse(port, {})
    verString = "2.5.7.11"

    dfu.setVersion(nCard, verString)

    calls = port.write.call_args_list

    req1 = json.loads(calls[2][0][0])
    assert req1["req"] == "dfu.status"
    assert req1["version"] == verString
