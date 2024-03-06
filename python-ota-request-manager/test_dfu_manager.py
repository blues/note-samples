import pytest
from unittest.mock import patch, MagicMock
from dfu import DFUManager, AuditLogFormatVersion
import dfu
from dfutypes import DFUType
from device import DeviceCache
from testutil import standardDeviceJSON, standardEnvironmentVars


def test_constructor_populatesDeviceCache():

    uid = 'my-device'
    d = DeviceCache(deviceJSON=standardDeviceJSON({'uid':uid}))

    m = DFUManager(d)

    assert m.device == d

def test_constructor_hasDefaultAuditLogFormat():

    
    d = MagicMock(spec=DeviceCache)

    m = DFUManager(d)

    assert m.AuditLogFormat == AuditLogFormatVersion.V1

def test_constructor_setsAuditLogFormat():
    d = MagicMock(spec=DeviceCache)


    manualFormat = AuditLogFormatVersion.V0
    m = DFUManager(d, auditLogFormat = manualFormat)

    assert m.AuditLogFormat == manualFormat

    manualFormat = AuditLogFormatVersion.V1
    m = DFUManager(d, auditLogFormat = manualFormat)

    assert m.AuditLogFormat == manualFormat


def test_requestUpdateToImage_imageFile_dfuEnvVarsSet():
    fileName = "myimage.bin"
    ts = 123
    d = DeviceCache(deviceJSON=standardDeviceJSON())

    m = DFUManager(d)

    with patch('dfu.generateDFUTimestamp') as gt:
        gt.return_value = ts
        m.requestUpdateToImage(fileName)

    assert m.device.getEnv(DFUManager.FIRMWARE_FILE_ENV) == fileName
    assert m.device.getEnv(DFUManager.RETRY_MAX_ENV, int) == 10
    assert m.device.getEnv(DFUManager.UPDATE_REQUEST_TS_ENV, int) == ts
    assert m.device.getEnv(DFUManager.RETRY_TS_ENV, int) == ts


def test_requestUpdateToImage_commentsUpdatedWithAuditLog():
    fileName = "myimage.bin"
    fwt = "user"
    localNotes = "hello"
    ts1 = 123
    ts2 = 456
    versionStr = "my_current_version"
    dfuInfo = {fwt:{"version":versionStr}}
    d = DeviceCache(deviceJSON=standardDeviceJSON({'dfu':dfuInfo}))

    m = DFUManager(d, auditLogFormat=AuditLogFormatVersion.V0)


    with patch('dfu.generateDFUTimestamp') as gt:
        gt.side_effect = [ts1, ts2]
        m.requestUpdateToImage(fileName,notes=localNotes)
        m.requestUpdateToImage(fileName,notes=localNotes)

    template = f"DFU LOG:\n{ts1},{fwt},{versionStr},{fileName},{ts1},10,0,,{localNotes}\n{ts2},{fwt},{versionStr},{fileName},{ts2},10,0,,{localNotes}"
    assert m.device.getEnv(DeviceCache.COMMENTS_ENVIRONMENT_VAR) == template

def test_requestUpdateToImage_commentsPreservedWithUpdatedAuditLog():
    commentStr = "my initial comment"
    fileName = "myimage.bin"
    fwt = "user"
    localNotes = "hello"
    ts1 = 123
    ts2 = 456
    versionStr = "my_current_version"
    dfuInfo = {fwt:{"version":versionStr}}
    d = DeviceCache(deviceJSON=standardDeviceJSON({'dfu':dfuInfo}))
    d.setEnvironmentVariablesFromJSON({DeviceCache.COMMENTS_ENVIRONMENT_VAR: commentStr})

    m = DFUManager(d, auditLogFormat=AuditLogFormatVersion.V0)

    with patch('dfu.generateDFUTimestamp') as gt:
        gt.side_effect = [ts1, ts2]
        m.requestUpdateToImage(fileName,notes=localNotes)
        m.requestUpdateToImage(fileName,notes=localNotes)

    template = f"DFU LOG:\n{ts1},{fwt},{versionStr},{fileName},{ts1},10,0,,{localNotes}\n{ts2},{fwt},{versionStr},{fileName},{ts2},10,0,,{localNotes}"
    comments = m.device.getEnv(DeviceCache.COMMENTS_ENVIRONMENT_VAR)
    assert comments.startswith(commentStr)
    assert comments.endswith(template)

