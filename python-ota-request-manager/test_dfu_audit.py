from unittest import TestCase
from dfu import auditlog, AuditLogFormatVersion
from dfu import logentry
from dfutypes import DFUType
import json

def test_logentry_constructor_requiredInputs_populatedProperties():

    e = logentry(3, DFUType.User, "myfile.bin")

    assert e.Id == 3
    assert e.Type == DFUType.User
    assert e.TargetFile == "myfile.bin"

def test_logentry_constructor_unrequiredInputsResultInDefaultPropertyValues():

    e = logentry(3, DFUType.User, "myfile.bin")

    assert e.RetryCount == 0
    assert e.RetryMax == 10
    assert e.Notes == ""
    assert e.LastRetry == None
    assert e.CancelledAt == None
    assert e.CurrentVersion == None



def test_parse_emptyString_emptyLog():
    s = ""
    log = auditlog.parse(s)

    assert log == []

def test_parse_noLogKey_emptyLog():
    notLogKey = "NON_LOG_KEY"
    assert notLogKey != auditlog.LOG_KEY
    s = f"ipsum etc.\n{notLogKey}\n"
    log = auditlog.parse(s)

    assert log == []


def test_parse_logKeyWithNoEntries_emptyLog():
    s = f"ipsum etc.\n{auditlog.LOG_KEY}\n\n"
    log = auditlog.parse(s)

    assert log == []

def test_parse_oneLogEntry_logWithOneElement():
    timestamp_id = 7
    dfu_type = DFUType.User
    current_ver = "1.2"
    filename = "dfu_file.bin"
    retry_ts = 11
    retry_max = 3
    retry_count = 2
    cancelled_ts = 0
    notes = "some basic notes about request"
    

    s = f"ipsum etc.\n{auditlog.LOG_KEY}\n{timestamp_id},{dfu_type},{current_ver},{filename},{retry_ts},{retry_max},{retry_count},{cancelled_ts},{notes}"

    log = auditlog.parse(s)

    
    assert isinstance(log, list)
    assert log[0].Id == timestamp_id
    assert log[0].Type == dfu_type
    assert log[0].CurrentVersion == current_ver
    assert log[0].TargetFile == filename
    assert log[0].RetryCount == retry_count
    assert log[0].RetryMax == retry_max
    assert log[0].LastRetry == retry_ts
    assert log[0].CancelledAt == cancelled_ts
    assert log[0].Notes == notes

    
    


def test_parse_multipleEntries_logWithMultipleElements():
    log1 = logentry(7, DFUType.User, "file_1.bin", retryMax=19, currentVersion="1.2")
    log1.CancelledAt = 23
    log1.LastRetry = 11
    log1.RetryCount = 13

    log2 = logentry(29, DFUType.Card, "file_2.bin", retryMax=41, currentVersion="2.3.5-dfuaxxxx", notes="some notes")
    log2.CancelledAt = 43
    log2.LastRetry = 31
    log2.RetryCount = 37

    expectedLog = [
                    log1,
                    log2
                     ]
    

    s = f"ipsum etc.\n{auditlog.LOG_KEY}\n{log1.Id},{log1.Type},{log1.CurrentVersion},{log1.TargetFile},{log1.LastRetry},{log1.RetryMax},{log1.RetryCount},{log1.CancelledAt},{log1.Notes}\n  {log2.Id} , {log2.Type} , {log2.CurrentVersion} , {log2.TargetFile} , {log2.LastRetry} , {log2.RetryMax} , {log2.RetryCount} , {log2.CancelledAt} , {log2.Notes} \n"

    log = auditlog.parse(s)

    
    assert isinstance(log, list)
    for i in range(len(log)):
        assert log[i].Id == expectedLog[i].Id
        assert log[i].Type == expectedLog[i].Type
        assert log[i].CurrentVersion == expectedLog[i].CurrentVersion
        assert log[i].TargetFile == expectedLog[i].TargetFile
        assert log[i].RetryCount == expectedLog[i].RetryCount
        assert log[i].RetryMax == expectedLog[i].RetryMax
        assert log[i].LastRetry == expectedLog[i].LastRetry
        assert log[i].CancelledAt == expectedLog[i].CancelledAt
        assert log[i].Notes == expectedLog[i].Notes


def test_parse_oneLogEntryJSONFormat_logWithOneElement():
    timestamp_id = 7
    dfu_type = DFUType.User
    current_ver = "1.2"
    filename = "dfu_file.bin"
    retry_ts = 11
    retry_max = 3
    retry_count = 2
    cancelled_ts = 0
    notes = "some basic notes about request"
    

    s = f'ipsum etc.\n{auditlog.LOG_KEY}\n{{"id":{timestamp_id},"type":"{dfu_type}","current_version":"{current_ver}","file":"{filename}","retry":{retry_ts},"retry_max":{retry_max},"retry_count":{retry_count},"cancelled":{cancelled_ts},"notes":"{notes}"}}'

    log = auditlog.parse(s)

    
    assert isinstance(log, list)
    assert log[0].Id == timestamp_id
    assert log[0].Type == dfu_type
    assert log[0].CurrentVersion == current_ver
    assert log[0].TargetFile == filename
    assert log[0].RetryCount == retry_count
    assert log[0].RetryMax == retry_max
    assert log[0].LastRetry == retry_ts
    assert log[0].CancelledAt == cancelled_ts
    assert log[0].Notes == notes


def test_parse_multipleEntriesJSONFormat_logWithMultipleElements():
    log1 = logentry(7, DFUType.User, "file_1.bin", retryMax=19, currentVersion="1.2")
    log1.CancelledAt = 23
    log1.LastRetry = 11
    log1.RetryCount = 13

    log2 = logentry(29, DFUType.Card, "file_2.bin", retryMax=41, currentVersion="2.3.5-dfuaxxxx", notes="some notes")
    log2.CancelledAt = 43
    log2.LastRetry = 31
    log2.RetryCount = 37

    expectedLog = [
                    log1,
                    log2
                     ]
    

    s = f'ipsum etc.\n{auditlog.LOG_KEY}\n[{{"id":{log1.Id},"type":"{log1.Type}","current_version":"{log1.CurrentVersion}","file":"{log1.TargetFile}","retry":{log1.LastRetry},"retry_max":{log1.RetryMax},"retry_count":{log1.RetryCount},"cancelled":{log1.CancelledAt},"notes":"{log1.Notes}"}},\n{{"id":{log2.Id},"type":"{log2.Type}","current_version":"{log2.CurrentVersion}","file":"{log2.TargetFile}","retry":{log2.LastRetry},"retry_max":{log2.RetryMax},"retry_count":{log2.RetryCount},"cancelled":{log2.CancelledAt},"notes":"{log2.Notes}"}}]'

    log = auditlog.parse(s)

    
    assert isinstance(log, list)
    for i in range(len(log)):
        assert log[i].Id == expectedLog[i].Id
        assert log[i].Type == expectedLog[i].Type
        assert log[i].CurrentVersion == expectedLog[i].CurrentVersion
        assert log[i].TargetFile == expectedLog[i].TargetFile
        assert log[i].RetryCount == expectedLog[i].RetryCount
        assert log[i].RetryMax == expectedLog[i].RetryMax
        assert log[i].LastRetry == expectedLog[i].LastRetry
        assert log[i].CancelledAt == expectedLog[i].CancelledAt
        assert log[i].Notes == expectedLog[i].Notes


def test_write_emptyLog_emptyString():
    log = []
    s = auditlog.write(log)

    assert s == ""


def test_write_singleLog_logHeaderAndLogEntry():
    log = logentry(7, DFUType.User, "file_1.bin", retryMax=19, currentVersion="1.2",notes="some notes")
    log.CancelledAt = 23
    log.LastRetry = 11
    log.RetryCount = 13
    
    
    expectedStr = f"{auditlog.LOG_KEY}\n7,user,1.2,file_1.bin,11,19,13,23,some notes"

    s = auditlog.write(log, AuditLogFormatVersion.V0)

    assert s == expectedStr

def test_write_multipleLog_logHeaderAndLogEntries():
    log1 = logentry(7, DFUType.User, "file_1.bin", retryMax=19, currentVersion="1.2")
    log1.CancelledAt = 23
    log1.LastRetry = 11
    log1.RetryCount = 13

    log2 = logentry(29, DFUType.Card, "file_2.bin", retryMax=41, currentVersion="2.3.5-dfuaxxxx", notes="some notes")
    log2.CancelledAt = 43
    log2.LastRetry = 31
    log2.RetryCount = 37

    logs = [
            log1,
            log2
                ]
    
    
    expectedStr = f"{auditlog.LOG_KEY}\n7,user,1.2,file_1.bin,11,19,13,23,\n29,card,2.3.5-dfuaxxxx,file_2.bin,31,41,37,43,some notes"

    s = auditlog.write(logs, AuditLogFormatVersion.V0)

    assert s == expectedStr

def test_write_singleLog_logHeaderAndLogEntryJSONFormat():
    log = logentry(7, DFUType.User, "file_1.bin", retryMax=19, currentVersion="1.2",notes="some notes")
    log.CancelledAt = 23
    log.LastRetry = 11
    log.RetryCount = 13
    
    expectedStr = f'\n{{"id":7,"type":"user","current_version":"1.2","file":"file_1.bin","retry":11,"retry_max":19,"retry_count":13,"cancelled":23,"notes":"some notes"}}'

    s = auditlog.write(log, formatVersion=AuditLogFormatVersion.V1)

    assert s.startswith(auditlog.LOG_KEY)

    s = s.removeprefix(auditlog.LOG_KEY)
    TestCase().assertDictEqual(json.loads(s), json.loads(expectedStr))

def test_write_multipleLog_logHeaderAndLogEntriesJSONFormat():
    log1 = logentry(7, DFUType.User, "file_1.bin", retryMax=19, currentVersion="1.2")
    log1.CancelledAt = 23
    log1.LastRetry = 11
    log1.RetryCount = 13

    log2 = logentry(29, DFUType.Card, "file_2.bin", retryMax=41, currentVersion="2.3.5-dfuaxxxx", notes="some notes")
    log2.CancelledAt = 43
    log2.LastRetry = 31
    log2.RetryCount = 37

    logs = [
            log1,
            log2
                ]
    expectedStr = f'\n[{{"id":7,"type":"user","current_version":"1.2","file":"file_1.bin","retry":11,"retry_max":19,"retry_count":13,"cancelled":23,"notes":""}},{{"id":29,"type":"card","current_version":"2.3.5-dfuaxxxx","file":"file_2.bin","retry":31,"retry_max":41,"retry_count":37,"cancelled":43,"notes":"some notes"}}]'

    s = auditlog.write(logs, formatVersion=AuditLogFormatVersion.V1)

    assert s.startswith(auditlog.LOG_KEY)

    s = s.removeprefix(auditlog.LOG_KEY)

    jExpected = json.loads(expectedStr)
    jActual = json.loads(s)
    for i in range(len(jExpected)):
        TestCase().assertDictEqual(jActual[i], jExpected[i] )

def test_hasID_logListWithMultipleIDs_returnsTrueIfIDValueExists():
    id1 = 2
    id2 = 3
    idMissing = 5
    logs = [logentry(id1, DFUType.User, "file1.bin"), 
            logentry(id2, DFUType.User, "file2.bin")]
    
    assert auditlog.hasID(logs, id1)
    assert auditlog.hasID(logs, id2)
    assert not auditlog.hasID(logs, idMissing)

def test_hasID_singleLog_returnsTrueIfIDValueExists():
    id1 = 2
    
    idMissing = 5
    logs = logentry(id1, DFUType.User, "file1.bin")
            
    
    assert auditlog.hasID(logs, id1)
    assert not auditlog.hasID(logs, idMissing)

def test_getIndexById_logListWithMultipleIDs_returnsIndex():
    id1 = 2
    id2 = 3
    
    logs = [logentry(id1, DFUType.User, "file1.bin"), 
            logentry(id2, DFUType.User, "file2.bin")]
    
    assert auditlog.getIndexById(logs, id1) == 0
    assert auditlog.getIndexById(logs, id2) == 1
    

def test_getIndexById_singleLog_returns0IfIdValueExists():
    id1 = 2
    
    idMissing = 5
    logs = logentry(id1, DFUType.User, "file1.bin")
            
    
    assert auditlog.getIndexById(logs, id1) == 0
    