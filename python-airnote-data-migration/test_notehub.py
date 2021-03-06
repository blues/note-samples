import pytest
import notehub
import json

from mock import patch, Mock

def test_getEventData():
    
    pin = "12345"
    deviceId = "dev:864475044207255"
    sinceEvent = "3a531360-577c-447f-b01f-d902014e6a36"

    with patch('requests.get') as mock_request:
            

            # set fake content
            mock_request.return_value.content = getTestResponse()

            d = notehub.getEventData(pin, deviceId, since=sinceEvent)

            assert d == json.loads(getTestResponse())

def test_getEventData_numericPin():
    
    pin = 12345
    deviceId = "dev:864475044207255"

    with patch('requests.get') as mock_request:
            

            # set fake content
            mock_request.return_value.content = '{"abc":"def"}'

            d = notehub.getEventData(pin, deviceId)

            header = mock_request.call_args[1]['headers']
            assert '12345' in header.values()


def test_getEventData_sinceIsAppendedToQueryString():
    
    pin = 12345
    deviceId = "dev:864475044207255"
    since = 'abcd'

    with patch('requests.get') as mock_request:
            

            # set fake content
            mock_request.return_value.content = '{"abc":"def"}'

            d = notehub.getEventData(pin, deviceId,since=since)

            urlUsed = mock_request.call_args[0][0]
            assert '&since=abcd' in urlUsed

def test_getEventData_pageSizeIsAppendedToQueryString():
    
    pin = 12345
    deviceId = "dev:864475044207255"
    pageSize = 17

    with patch('requests.get') as mock_request:
            

            # set fake content
            mock_request.return_value.content = '{"abc":"def"}'

            d = notehub.getEventData(pin, deviceId,pageSize=pageSize)

            urlUsed = mock_request.call_args[0][0]
            assert '&pageSize=17' in urlUsed

def test_getEventData_deviceIdIsAppendedToQueryString():
    
    pin = 12345
    deviceId = "dev:864475044207255"
    pageSize = 17

    with patch('requests.get') as mock_request:
            

            # set fake content
            mock_request.return_value.content = '{"abc":"def"}'

            d = notehub.getEventData(pin, deviceId,pageSize=pageSize)

            urlUsed = mock_request.call_args[0][0]
            assert 'deviceUIDs=dev:864475044207255' in urlUsed
    
def test_migrateAirnoteData():
    
    pin = "12345"
    deviceId = "dev:864475044207255"

    with patch('requests.get') as mock_request:
            

            # set fake content
            mock_request.return_value.content = responseWithOneEventAndNoMoreWaiting()
            m = Mock()
            notehub.migrateAirnoteData(pin, deviceId, migrateFunc=m)
            a = json.loads(singleEvent)
            m.assert_called_once_with(a)

def test_migrateAirnoteData_multipleEvents():
    
    pin = "12345"
    deviceId = "dev:864475044207255"

    with patch('notehub.getEventData') as mock_getEventData:
            
            mock_getEventData.return_value = {"has_more":False,"through":"abcd","events":[{"file":"_air.qo"},{"file":"_air.qo"},{"file":"other.qo"}]}
            m = Mock()
            notehub.migrateAirnoteData(pin, deviceId, migrateFunc=m)
            assert m.call_count == 2


def test_migrateAirnoteData_multipleApiCalls():
    
    pin = "12345"
    deviceId = "dev:864475044207255"

    with patch('notehub.getEventData') as mock_getEventData:
            
            mock_getEventData.side_effect = [
                {"has_more":True,"through":"abcd","events":[{"file":"_air.qo"}]},
                {"has_more":False,"through":"defg","events":[{"file":"_air.qo"}]},
            ]
            m = Mock()
            notehub.migrateAirnoteData(pin, deviceId, migrateFunc=m)
            assert m.call_count == 2

def test_migrateAirnoteData_usesLastEventInfoForNextRequest():
    
    pin = "12345"
    deviceId = "dev:864475044207255"

    with patch('notehub.getEventData') as mock_getEventData:
            
            mock_getEventData.side_effect = [
                {"has_more":True,"through":"abcd","events":[{"file":"_air.qo"}]},
                {"has_more":False,"through":"defg","events":[{"file":"_air.qo"}]},
            ]
            m = Mock()
            notehub.migrateAirnoteData(pin, deviceId, migrateFunc=m)
            mock_getEventData.assert_called_with(pin, deviceId, since='abcd',pageSize=50)


def test_migrateAirnoteData_hasMoreFails():
    
    pin = "12345"
    deviceId = "dev:864475044207255"

    with patch('notehub.getEventData') as mock_getEventData:
            
            mock_getEventData.side_effect = [
                {"through":"defg","events":[{"file":"_air.qo"}]},
            ]
            m = Mock()
            notehub.migrateAirnoteData(pin, deviceId, migrateFunc=m)
            assert m.call_count == 0


def test_migrateAirnoteData_maxCalls():
    
    pin = "12345"
    deviceId = "dev:864475044207255"

    with patch('notehub.getEventData') as mock_getEventData:
            
            mock_getEventData.side_effect = [
                {"has_more":True,"through":"abcd","events":[{"file":"_air.qo"}]},
                {"has_more":False,"through":"defg","events":[{"file":"_air.qo"}]},
            ]
            m = Mock()
            notehub.migrateAirnoteData(pin, deviceId, migrateFunc=m, max_requests=1)
            assert m.call_count == 1


singleEvent = '''{
                "uid": "49b8fcf4-c439-4177-a5a4-39bbe3ded4a9",
                "device_uid": "dev:864475044207255",
                "file": "_air.qo",
                "captured": "2020-01-01T01:25:40Z",
                "received": "2021-04-08T06:23:41Z",
                "body": {
                    "csecs": 484,
                    "sensor": "lnd712",
                    "temperature": 0.01,
                    "voltage": 3.9785156
                },
                "gps_location": {
                    "when": "2021-04-08T06:23:35Z",
                    "name": "Johor Bahru, Johor",
                    "country": "MY",
                    "timezone": "Asia/Kuala_Lumpur",
                    "latitude": 1.516745,
                    "longitude": 103.733556
                }
                }'''
def responseWithOneEventAndNoMoreWaiting():
    r = '''{
            "events":[''' + singleEvent + '''
                
            ],
            "has_more":false,
            "through":"49b8fcf4-c439-4177-a5a4-39bbe3ded4a9"
        }'''
    return r


def getTestResponse():
    r = '''
    {
        "through": "ee0f7c1b-754c-4a4b-84fe-07cf3d96ec53",
        "has_more": true,
        "events": [
            {
                "uid": "3a531360-577c-447f-b01f-d902014e6a37",
                "device_uid": "dev:864475044207255",
                "file": "_env.dbs",
                "captured": "2020-01-01T00:05:15Z",
                "received": "2021-04-08T04:24:40Z",
                "body": {
                    "card": {
                    "type": "card",
                    "version": "{\\"org\\":\\"Blues Wireless\\",\\"product\\":\\"Notecard\\",\\"version\\":\\"notecard-1.5.4\\",\\"ver_major\\":1,\\"ver_minor\\":5,\\"ver_patch\\":4,\\"ver_build\\":12695,\\"built\\":\\"Apr  5 2021 13:34:56\\""
                    },
                    "modem": {
                    "type": "modem"
                    },
                    "user": {
                    "type": "user"
                    }
                },
                "tower_location": {
                    "when": "2021-04-08T04:24:14Z",
                    "name": "Johor Bahru, Johor",
                    "country": "MY",
                    "timezone": "Asia/Kuala_Lumpur",
                    "latitude": 1.516745,
                    "longitude": 103.733556
                },
                "gps_location": null
           },
            {
            "uid": "7c83b38b-bf3d-460d-bbbd-d8e90cdabff4",
            "device_uid": "dev:864475044207255",
            "file": "_air.qo",
            "captured": "2020-01-01T00:09:52Z",
            "received": "2021-04-08T04:30:39Z",
            "body": {
                "csecs": 482,
                "motion": 45,
                "sensor": "lnd712",
                "temperature": 0.01,
                "voltage": 3.9765625
            },
            "tower_location": {
                "when": "2021-04-08T04:30:34Z",
                "name": "Johor Bahru, Johor",
                "country": "MY",
                "timezone": "Asia/Kuala_Lumpur",
                "latitude": 1.514572,
                "longitude": 103.734272
            },
            "gps_location": null
            },
            {
            "uid": "3447589a-9724-43fd-92e2-e590fe28e603",
            "device_uid": "dev:864475044207255",
            "file": "_air.qo",
            "captured": "2020-01-01T00:34:44Z",
            "received": "2021-04-08T06:23:40Z",
            "body": {
                "csecs": 484,
                "motion": 31,
                "sensor": "lnd712",
                "temperature": 0.01,
                "voltage": 3.9667969
            },
            "tower_location": {
                "when": "2021-04-08T06:23:35Z",
                "name": "Johor Bahru, Johor",
                "country": "MY",
                "timezone": "Asia/Kuala_Lumpur",
                "latitude": 1.516745,
                "longitude": 103.733556
            },
            "gps_location": null
            },
            {
            "uid": "49b8fcf4-c439-4177-a5a4-39bbe3ded4a9",
            "device_uid": "dev:864475044207255",
            "file": "_air.qo",
            "captured": "2020-01-01T01:25:40Z",
            "received": "2021-04-08T06:23:41Z",
            "body": {
                "csecs": 484,
                "sensor": "lnd712",
                "temperature": 0.01,
                "voltage": 3.9785156
            },
            "tower_location": {
                "when": "2021-04-08T06:23:35Z",
                "name": "Johor Bahru, Johor",
                "country": "MY",
                "timezone": "Asia/Kuala_Lumpur",
                "latitude": 1.516745,
                "longitude": 103.733556
            },
            "gps_location": null
            }
        ]
    }'''

    return r
