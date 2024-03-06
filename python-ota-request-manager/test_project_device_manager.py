import pytest
from unittest import TestCase
from unittest.mock import MagicMock, patch
from device import DeviceCache
from notehub import NotehubProject
from notehub import ProjectDeviceManager
from testutil import standardDeviceJSON, standardEnvironmentVars

def test_constructor_setNotehubProjectConnection():

    p = MagicMock(spec=NotehubProject)

    m = ProjectDeviceManager(p)

    assert m._project == p


def test_updateDevice_fromDeviceCache_noChanges_doNothing():
    p = MagicMock(spec=NotehubProject)
    m = ProjectDeviceManager(p)

    d = DeviceCache(uid="random-uid")
    d.setEnvironmentVariablesFromJSON({"var1":"value1"})

    m.updateDevice(d)

    p.setDeviceEnvironmentVars.assert_not_called()
    p.provisionDevice.assert_not_called()
    p.deleteDevice.assert_not_called()
    p.enableDevice.assert_not_called()
    p.disableDevice.assert_not_called()
    p.enableDeviceConnectivityAssurance.assert_not_called()
    p.disableDeviceConnectivityAssurance.assert_not_called()


def test_updateDevice_force_noChanges_callNotehubAPI():
    p = MagicMock(spec=NotehubProject)
    m = ProjectDeviceManager(p)

    d = DeviceCache(uid="random-uid")
    d.setEnvironmentVariablesFromJSON({"var1":"value1"})

    m.updateDevice(d, force=True)

    p.setDeviceEnvironmentVars.assert_called_once_with("random-uid", {"var1":"value1"})
   

def test_updateDevice_changeEnvironmentVar_callAPIToChangeEnvVars():
    p = MagicMock(spec=NotehubProject)
    m = ProjectDeviceManager(p)
    uid = "random-uid"
    d = DeviceCache(uid=uid)
    d.setEnvironmentVariablesFromJSON({"var1":"value1"})

    d.setEnv("var1", "value2")

    m.updateDevice(d)

    p.setDeviceEnvironmentVars.assert_called_once_with(uid, {"var1":"value2"})

def test_fetchDevice_singleDeviceUID_deviceCacheCreatedWithResultingJSON():
    uid = "my-uid"
    json = standardDeviceJSON({'uid':uid})

    p = MagicMock(spec=NotehubProject)
    p.getDeviceInfo.return_value = json
    m = ProjectDeviceManager(p)

    d = m.fetchDevice(uid)

    assert d.UID == uid


def test_fetchDevice_singleDeviceUID_deviceCacheHasDeviceEnvVars():
    uid = 'random-uid'
    json = standardDeviceJSON({'uid':uid})
    v = {'var1':'value1'}
    envVars = standardEnvironmentVars(v)
    p = MagicMock(spec=NotehubProject)
    p.getDeviceInfo.return_value = json
    p.getDeviceEnvironmentVars.return_value = envVars
    m = ProjectDeviceManager(p)

    d = m.fetchDevice(uid)

    TestCase().assertDictEqual(d.getEnv(), v)



def test_fetchDevice_singleDeviceUID_hasNoEnvVars():
    uid = 'random-uid'
    json = standardDeviceJSON({'uid':uid})
    v = {}
    envVars = standardEnvironmentVars(v)
    p = MagicMock(spec=NotehubProject)
    p.getDeviceInfo.return_value = json
    p.getDeviceEnvironmentVars.return_value = envVars
    m = ProjectDeviceManager(p)

    d = m.fetchDevice(uid)

    TestCase().assertDictEqual(d.getEnv(), v)

def test_fetchDevice_multipleDeviceUIDs():
    uid1 = 'random-uid-1'
    uid2 = 'random-uid-2'
    envVars = standardEnvironmentVars({})
    p = MagicMock(spec=NotehubProject)
    p.getDeviceInfo.side_effect = [standardDeviceJSON({'uid':uid1}), standardDeviceJSON({'uid':uid2})]
    p.getDeviceEnvironmentVars.return_value = envVars
    m = ProjectDeviceManager(p)

    d = m.fetchDevice([uid1, uid2])

    assert isinstance(d, list)
    assert d[0].UID == uid1
    assert d[1].UID == uid2







