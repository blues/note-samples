from dfutypes import DFUType
from device import DeviceCache
import time
import json

DEFAULT_RETRY_MAX = 10

class logentry:

    def __init__(self, id:int, type:DFUType, targetFile:str, retryMax:int=DEFAULT_RETRY_MAX, notes:str="", currentVersion:str=None) -> None:

        self.Id = id
        self.Type = type
        self.TargetFile = targetFile
        self.RetryCount = 0
        self.RetryMax = retryMax
        self.Notes = notes
        self.LastRetry = None
        self.CancelledAt = None
        self.CurrentVersion = currentVersion


class AuditLogFormatVersion:
    V0 = "v0"
    V1 = "v1"

class auditlog:
    LOG_KEY = "DFU LOG:"
    LOG_ITEM_SEPARATOR=","
    LOG_ENTRY_SEPARATOR = "\n"
    LOG_ENTRY_JSON_SCHEMA = {"Id":"id", "Type":"type","TargetFile":"file", "LastRetry":"retry", "RetryCount":"retry_count","RetryMax":"retry_max", "Notes":"notes", "CancelledAt":"cancelled", "CurrentVersion":"current_version"}

    @staticmethod
    def _parseV0(content):
        lines = content.split(auditlog.LOG_ENTRY_SEPARATOR)

        log = []
        for line in lines:
        
            r = line.split(auditlog.LOG_ITEM_SEPARATOR)
            r = [s.strip() for s in r]
            id = int(r[0])
            t = r[1]
            v = r[2]
            f = r[3]
            rl = int(r[4])
            rm = int(r[5])
            rc = int(r[6])
            ct = None if r[7] == '' else int(r[7])
            n = r[8]

            entry = logentry(id, t, f, currentVersion=v, retryMax=rm, notes=n)
            entry.LastRetry = rl
            entry.RetryCount = rc
            entry.CancelledAt = ct
            
            log.append(entry)

        return log
    
    def _parseV1(content):
        a = json.loads(content)


        
        if not isinstance(a, list):
            a = [a]

        
        log = []
        for j in a:
            entry = logentry(None, None, None)
            
            for p,k in auditlog.LOG_ENTRY_JSON_SCHEMA.items():
                setattr(entry, p, j.get(k))

            log.append(entry)

        return log
    
    @staticmethod
    def parse(content:str):

        if auditlog.LOG_KEY not in content:
            return []
        
        r = content.split(auditlog.LOG_KEY,1)
        content = str.strip(r[1])

        if content == "":
            return []
        
        if content.startswith("[") or content.startswith("{"):
            return auditlog._parseV1(content)

        return auditlog._parseV0(content)

    @staticmethod
    def _writeV0(log):

        s = auditlog.LOG_KEY

        for entry in log:
            id = entry.Id
            type=entry.Type
            version = entry.CurrentVersion
            file=entry.TargetFile
            last_retry = entry.LastRetry
            retry_count = entry.RetryCount
            retry_max=entry.RetryMax
            cancelled_ts = '' if  entry.CancelledAt is None else entry.CancelledAt
            notes = entry.Notes

            p = auditlog.LOG_ITEM_SEPARATOR
            s +=f"{auditlog.LOG_ENTRY_SEPARATOR}{id}{p}{type}{p}{version}{p}{file}{p}{last_retry}{p}{retry_max}{p}{retry_count}{p}{cancelled_ts}{p}{notes}"


        return s
    
    @staticmethod
    def _writeV1(log):


        s = auditlog.LOG_KEY

        # for entry in log:
        #     id = entry.Id
        #     type=entry.Type
        #     version = entry.CurrentVersion
        #     file=entry.TargetFile
        #     last_retry = entry.LastRetry
        #     retry_count = entry.RetryCount
        #     retry_max=entry.RetryMax
        #     cancelled_ts = '' if  entry.CancelledAt is None else entry.CancelledAt
        #     notes = entry.Notes

        #     p = auditlog.LOG_ITEM_SEPARATOR
        #     s +=f"{auditlog.LOG_ENTRY_SEPARATOR}{id}{p}{type}{p}{version}{p}{file}{p}{last_retry}{p}{retry_max}{p}{retry_count}{p}{cancelled_ts}{p}{notes}"
        jsonEntries = []
        for entry in log:
            e = {}
            for p,k in auditlog.LOG_ENTRY_JSON_SCHEMA.items():
                e[k] = getattr(entry, p)

            jsonEntries.append(e)
        
        jsonStr = json.dumps(jsonEntries[0], separators=(',',':')) if len(jsonEntries) == 1 else json.dumps(jsonEntries, separators=(',',':'))

        s = s + "\n" + jsonStr
        return s
    
    @staticmethod
    def write(log, formatVersion = AuditLogFormatVersion.V1):

        
        if not isinstance(log, list):
            log = [log]

        if len(log) < 1:
            return ""


        if formatVersion == AuditLogFormatVersion.V0:
            return auditlog._writeV0(log)
        
        
        return auditlog._writeV1(log)
       

    def hasID(log, id):
        if not isinstance(log, list):
            log = [log]

        for item in log:
            if item.Id == id:
                return True
            
        return False
    
    def getIndexById(log, id):
        if not isinstance(log, list):
            log = [log]

        for i in range(len(log)):
            if log[i].Id == id:
                return i
            
        return None


def generateDFUTimestamp():
    return int(time.time())

class DFUManager:
    FIRMWARE_FILE_ENV = "firmware_file"
    RETRY_TS_ENV = "retry_ts"
    RETRY_MAX_ENV = "retry_max"
    RETRY_COUNT_ENV = "retry_count"
    UPDATE_REQUEST_TS_ENV = "update_ts"
    FIRMWARE_TYPE = "user"

    def __init__(self, deviceCache, auditLogFormat=AuditLogFormatVersion.V1) -> None:
        
        self.device = deviceCache
        self.AuditLogFormat = auditLogFormat

    def requestUpdateToImage(self, fileName, retryMax=DEFAULT_RETRY_MAX, notes=""):
        ts = generateDFUTimestamp()
        currentVer = self.device.getVersionStr(self.FIRMWARE_TYPE)
        comments = self.device.getEnv(DeviceCache.COMMENTS_ENVIRONMENT_VAR)
        
        auditLog = [] if comments is None else auditlog.parse(comments)

        self.device.setEnv(self.FIRMWARE_FILE_ENV, fileName)
        self.device.setEnv(self.RETRY_MAX_ENV, retryMax)
        self.device.setEnv(self.RETRY_TS_ENV, ts)
        self.device.setEnv(self.UPDATE_REQUEST_TS_ENV, ts)

        logEntry = logentry(ts, 
                            self.FIRMWARE_TYPE, 
                            fileName, 
                            retryMax=retryMax,
                            notes=notes,
                            currentVersion=currentVer)
        logEntry.LastRetry= ts

        auditLog.append(logEntry)

        s = auditlog.write(auditLog, self.AuditLogFormat)
        
        
        if comments is not None:
            header = comments
            if auditlog.LOG_KEY in comments:
                r = comments.split(auditlog.LOG_KEY,1)
                header = str.strip(r[0])
            if header != "":
                s = "\n".join([header, s])

        self.device.setEnv(DeviceCache.COMMENTS_ENVIRONMENT_VAR, s)


    def requestUpdateRetry(self):
        pass


HOST_DFU_RETRY_COUNT_LABEL = "_fw_retry_count"
HOST_DFU_RETRY_LABEL = "_fw_retry"
HOST_DFU_FILE_LABEL = "_fw"
HOST_DFU_RETRY_ATTEMPT_MAX_LABEL = "_fw_retry_max"
HOST_DFU_REQUEST_TS_LABEL = "_fw_requested_at"

CARD_DFU_RETRY_COUNT_LABEL = "_fwc_retry_count"
CARD_DFU_RETRY_LABEL = "_fwc_retry"
CARD_DFU_FILE_LABEL = "_fwc"
CARD_DFU_RETRY_ATTEMPT_MAX_LABEL = "_fwc_retry_max"
CARD_DFU_REQUEST_TS_LABEL = "_fwc_requested_at"

class HostUpdateManager(DFUManager):
    FIRMWARE_FILE_ENV = HOST_DFU_FILE_LABEL
    RETRY_TS_ENV = HOST_DFU_RETRY_LABEL
    RETRY_MAX_ENV = HOST_DFU_RETRY_ATTEMPT_MAX_LABEL
    RETRY_COUNT_ENV = HOST_DFU_RETRY_COUNT_LABEL
    UPDATE_REQUEST_TS_ENV = HOST_DFU_REQUEST_TS_LABEL
    FIRMWARE_TYPE = "user"
 
class NotecardUpdateManager(DFUManager):
    FIRMWARE_FILE_ENV = CARD_DFU_FILE_LABEL
    RETRY_TS_ENV = CARD_DFU_RETRY_LABEL
    RETRY_MAX_ENV = CARD_DFU_RETRY_ATTEMPT_MAX_LABEL
    RETRY_COUNT_ENV = CARD_DFU_RETRY_COUNT_LABEL
    UPDATE_REQUEST_TS_ENV = CARD_DFU_REQUEST_TS_LABEL
    FIRMWARE_TYPE = "card"
