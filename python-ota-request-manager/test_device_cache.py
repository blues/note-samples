import pytest
from unittest import TestCase
from device import DeviceCache
from datetime import datetime, timezone
from testutil import standardDeviceJSON, standardEnvironmentVars


def test_fromV1JSON_singleDeviceJSONObject():

    json = standardDeviceJSON()

    d = DeviceCache.fromV1JSON(json)

    TestCase().assertDictEqual(d._device_json, json)

    

def test_fromV1JSON_arrayOfDeviceObjects():
    devJSON1 = standardDeviceJSON()
    devJSON2 = standardDeviceJSON({'uid':"dev:123456789"})

    json = {"devices": [devJSON1,devJSON2]}

    d = DeviceCache.fromV1JSON(json)

    assert isinstance(d, list)

    TestCase().assertDictEqual(d[0]._device_json, devJSON1)
    TestCase().assertDictEqual(d[1]._device_json, devJSON2)

    assert d[0].UID == devJSON1['uid']
    assert d[1].UID == devJSON2['uid']

def test_UID_readonly():
    uid = "dev:my-uid"
    json = standardDeviceJSON({'uid':uid})
    d = DeviceCache.fromV1JSON(json)

    assert d.UID == json['uid']
    
    d = DeviceCache(uid = uid)

    assert d.UID == json['uid']




def test_SerialNumber():
    sn = "abc:123"
    json = standardDeviceJSON({"serial_number": sn})

    d = DeviceCache.fromV1JSON(json)

    assert d.SerialNumber == sn

    newSN = "def:567"

    d.SerialNumber = newSN

    assert d.SerialNumber == newSN
    

    d = DeviceCache(uid="random-uid")
    d.SerialNumber = sn

    assert d.SerialNumber == sn

def test_SerialNumberChanged():
    sn = "abc:123"
    newSN = "def:456"
    json = standardDeviceJSON({"serial_number": sn})

    d = DeviceCache.fromV1JSON(json)

    d.SerialNumber = sn

    assert not d.SerialNumberIsChanged

    d.SerialNumber = newSN

    assert d.SerialNumberIsChanged


def test_setEnvironmentVariablesFromJSON():
    nv = {"name1":"value1","name2":"3.14"}
   

    d = DeviceCache(uid='random-uid')
    d.setEnvironmentVariablesFromJSON(nv)

    TestCase().assertDictEqual(d._environment_vars_cache, nv)

    e = standardEnvironmentVars(nv)
    d.setEnvironmentVariablesFromJSON(e)

    TestCase().assertDictEqual(d._environment_vars_cache, nv)
    

def test_getEnv():
    nv = {"strVar":"my-value", "numVar":"357"}
    d = DeviceCache(uid="random-uid")
    d.setEnvironmentVariablesFromJSON(nv)


    assert d.getEnv("strVar") == "my-value"
    assert d.getEnv("numVar") == "357"
    assert d.getEnv("numVar", int) == 357

def test_getEnv_noVarExists_returnsNone():
    d = DeviceCache(uid="random-uid")

    assert d.getEnv("myVar") is None

def test_getEnv_noInput_returnsAll():
    d = DeviceCache(uid="random-uid")
    d.setEnv("name1", "value1")
    d.setEnv("name2", "value2")

    TestCase().assertDictEqual({"name1":"value1","name2":"value2"}, d.getEnv())

def test_deleteEnv():
    nv = {"strVar":"my-value", "numVar":"357"}
    d = DeviceCache(uid="random-uid")
    d.setEnvironmentVariablesFromJSON(nv)

    d.deleteEnv("strVar")

    assert d.getEnv("strVar") is None

def test_setEnv():
    d = DeviceCache(uid="random-uid")

    n = "name1"
    v = "value1"

    assert d.getEnv(n) is None
    
    d.setEnv(n, v)

    assert d.getEnv(n) == v

    v = 314
    d.setEnv(n, v)

    assert d.getEnv(n) == str(v)

def test_EnvironmentVarsIsChanged_envVarAdded():
    nv = {"strVar":"my-value", "numVar":"357"}
    d = DeviceCache(uid="random-uid")
    d.setEnvironmentVariablesFromJSON(nv)

    assert not d.EnvironmentVarsIsChanged

    d.setEnv("my-var", "my-value")

    assert d.EnvironmentVarsIsChanged


def test_EnvironmentVarsIsChanged_envVarRemoved():
    nv = {"strVar":"my-value", "numVar":"357"}
    d = DeviceCache(uid="random-uid")
    d.setEnvironmentVariablesFromJSON(nv)

    assert not d.EnvironmentVarsIsChanged

    d.deleteEnv("strVar")

    assert d.EnvironmentVarsIsChanged


def test_EnvironmentVarsIsChanged_envVarValueChanged():
    nv = {"strVar":"my-value", "numVar":"357"}
    d = DeviceCache(uid="random-uid")
    d.setEnvironmentVariablesFromJSON(nv)

    assert not d.EnvironmentVarsIsChanged

    d.setEnv("strVar", "my-new-value")

    assert d.EnvironmentVarsIsChanged

def test_Tags_noTags_emptySet():
    d = DeviceCache(uid="random-uid")

    assert d.Tags == set()

    d.setEnv(DeviceCache.TAGS_ENVIRONMENT_VAR, "")

    assert d.Tags == set()

def test_Tags_returnsSetOfTags():
    d1 = DeviceCache(uid="random-uid")
    sep = DeviceCache.TAG_SEPARATOR
    tagStr = f"tag 1 {sep}tag 2 \r{sep}tag 3 {sep}tag 1{sep}{sep}tag 4"
    expectedTags = set(["tag 1", "tag 2", "tag 3", "tag 4"])
    json = standardEnvironmentVars({DeviceCache.TAGS_ENVIRONMENT_VAR: tagStr})
    d1.setEnvironmentVariablesFromJSON(json)
    
    t = d1.Tags
    assert t == expectedTags

    d2 = DeviceCache(uid="random-uid")
    
    d2.setEnv(DeviceCache.TAGS_ENVIRONMENT_VAR, tagStr)

    assert d2.Tags == expectedTags


def test_set_Tags_value():
    d = DeviceCache(uid="random-uid")
    json = standardEnvironmentVars({DeviceCache.TAGS_ENVIRONMENT_VAR: "original_tag"})
    d.setEnvironmentVariablesFromJSON(json)

    assert d.Tags == set(["original_tag"])

    d.Tags = ["a", "b", "c"]

    assert d.Tags == set(["a", "b", "c"])
    sep = DeviceCache.TAG_SEPARATOR
    assert d.getEnv(DeviceCache.TAGS_ENVIRONMENT_VAR) == f"a{sep}b{sep}c"

    d.Tags = set(["d", "e", "f"])

    assert d.Tags == set(["f", "e", "d"])
    sep = DeviceCache.TAG_SEPARATOR
    assert d.getEnv(DeviceCache.TAGS_ENVIRONMENT_VAR) == f"d{sep}e{sep}f"

def test_addTags():
    d = DeviceCache(uid="random-uid")

    d.addTags(["a", "b"])

    assert d.Tags == set(["a", "b"])

    d.addTags(["c"])

    assert d.Tags == set(["a", "b", "c"])

    d.addTags("def")

    assert d.Tags == set(["a", "b", "c", "def"])

def test_removeTags():
    d = DeviceCache(uid="random-uid")
    d.Tags = ["a", "b", "c", "def"]

    assert d.Tags == set(["a", "b", "c", "def"])

    d.removeTags("not-a-tag")

    assert d.Tags == set(["a", "b", "c", "def"])

    d.removeTags("a")

    assert d.Tags == set(["b", "c", "def"])

    d.removeTags(["a", "b", "c"])

    assert d.Tags == set(["def"])

    d.removeTags("def")

    assert d.Tags == set()

def test_Comments_noCommentsAvailable_returnsNone():
    d = DeviceCache(uid="random-uid")

    assert d.Comments is None

    d.setEnvironmentVariablesFromJSON(standardEnvironmentVars({"var1":"val1"}))

    assert d.Comments is None


def test_Comments_CommentsAvailable_returnsAsString():
    d = DeviceCache(uid="random-uid")
    d.setEnvironmentVariablesFromJSON(standardEnvironmentVars({DeviceCache.COMMENTS_ENVIRONMENT_VAR:"comments 1"}))

    assert d.Comments == "comments 1"

    d.setEnv(DeviceCache.COMMENTS_ENVIRONMENT_VAR, "comments 2")

    assert d.Comments == "comments 2"

def test_set_Comments():
    d = DeviceCache(uid="random-uid")
    commentStr = "comments new"
    d.setEnvironmentVariablesFromJSON(standardEnvironmentVars({DeviceCache.COMMENTS_ENVIRONMENT_VAR:"comments 1"}))

    d.Comments = commentStr

    assert d.Comments == commentStr

    d.setEnv(DeviceCache.COMMENTS_ENVIRONMENT_VAR, "comments 2")

    d.Comments = commentStr

    assert d.Comments == commentStr

def test_ProvisionedDate_readonly():

    dt = datetime(2019, 5, 18, 15, 17, tzinfo=timezone.utc)
    dtStr = dt.isoformat()
    deviceJSON = standardDeviceJSON({'provisioned': dtStr})
    d = DeviceCache(deviceJSON=deviceJSON)

    assert d.ProvisionedDate == dt

def test_ProvisionedDate_noDateAvailable_returnsNone():
    d = DeviceCache(uid = "random-uid")

    assert d.ProvisionedDate is None

def test_IsProvisioned_readonly():

    d = DeviceCache(uid = "random-uid")

    assert not d.IsProvisioned


    d = DeviceCache(deviceJSON = standardDeviceJSON())

    assert d.IsProvisioned

def test_NotecardVersionStr_noVersionInfo_returnsNone():

    d = DeviceCache(uid = "random-uid")

    assert d.NotecardVersionStr is None

def test_NotecardVersionStr_returnsStr():
    v = "my-version-str"
    dfuObj = {"card":{"version":f'{{"version":"{v}"}}'}}

    d = DeviceCache(deviceJSON=standardDeviceJSON({'dfu':dfuObj}))

    assert d.NotecardVersionStr == v

def test_HostVersionStr_noVersionInfo_returnsNone():

    d = DeviceCache(uid = "random-uid")

    assert d.HostVersionStr is None

def test_HostVersionStr_returnsStr():
    v = "my-version-str"
    dfuObj = {"user":{"version":v}}

    d = DeviceCache(deviceJSON=standardDeviceJSON({'dfu':dfuObj}))

    assert d.HostVersionStr == v

def test_getDFUInfo_noInfoAvailable_returnsNone():

    d = DeviceCache(uid = "random-uid")

    assert d.getDFUInfo("card") is None
    assert d.getDFUInfo("user") is None

def test_getDFUInfo_invalidType_raisesException():
    d = DeviceCache(uid = "random-uid")

    with pytest.raises(Exception):
        d.getDFUInfo("non-valid-type")


def test_getDFUInfo_readOnly():
    dfuInfo = {"a":"b"}
    dfuObj = {"user":dfuInfo}

    d = DeviceCache(deviceJSON=standardDeviceJSON({'dfu':dfuObj}))

    TestCase().assertDictEqual(d.getDFUInfo("user"), dfuInfo)

def test_getVersionString():

    hostVer = "host-version-str"
    cardVer = "card-version-str"
    dfuObj = {"user":{"version":hostVer},"card":{"version":f'{{"version":"{cardVer}"}}'}}

    d = DeviceCache(deviceJSON=standardDeviceJSON({'dfu':dfuObj, 'uid':'random-uid'}))

    assert d.getVersionStr("user") == hostVer
    assert d.getVersionStr("card") == cardVer

    









    






    

    





    

    

















