import pytest
import notehub
import json

from mock import patch, Mock

def test_getEventData():
    
    pin = "12345"
    deviceId = "dev:864475044207255"
    cursorID = "3a531360-577c-447f-b01f-d902014e6a36"

    with patch('requests.get') as mock_request:
            

            # set fake content
            mock_request.return_value.content = getTestResponse()

            d = notehub.getEventData(pin, deviceId, cursor=cursorID)

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


def test_getEventData_cursorIsAppendedToQueryString():
    
    pin = 12345
    deviceId = "dev:864475044207255"
    cursorID = 'abcd'

    with patch('requests.get') as mock_request:
            

            # set fake content
            mock_request.return_value.content = '{"abc":"def"}'

            d = notehub.getEventData(pin, deviceId,cursor=cursorID)

            urlUsed = mock_request.call_args[0][0]
            assert '&cursor=abcd' in urlUsed

def test_getEventData_limitIsAppendedToQueryString():
    
    pin = 12345
    deviceId = "dev:864475044207255"
    limit = 17

    with patch('requests.get') as mock_request:
            

            # set fake content
            mock_request.return_value.content = '{"abc":"def"}'

            d = notehub.getEventData(pin, deviceId,limit=limit)

            urlUsed = mock_request.call_args[0][0]
            assert '&limit=17' in urlUsed

def test_getEventData_deviceIdIsAppendedToQueryString():
    
    pin = 12345
    deviceId = "dev:864475044207255"
    pageSize = 17

    with patch('requests.get') as mock_request:
            

            # set fake content
            mock_request.return_value.content = '{"abc":"def"}'

            d = notehub.getEventData(pin, deviceId,limit=pageSize)

            urlUsed = mock_request.call_args[0][0]
            assert 'deviceUID=dev:864475044207255' in urlUsed
    
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
            
            mock_getEventData.return_value = {"has_more":False,"next_cursor":"","events":[{"file":"_air.qo"},{"file":"_air.qo"},{"file":"other.qo"}]}
            m = Mock()
            notehub.migrateAirnoteData(pin, deviceId, migrateFunc=m)
            assert m.call_count == 2


def test_migrateAirnoteData_multipleApiCalls():
    
    pin = "12345"
    deviceId = "dev:864475044207255"

    with patch('notehub.getEventData') as mock_getEventData:
            
            mock_getEventData.side_effect = [
                {"has_more":True,"next_cursor":"abcd","events":[{"file":"_air.qo"}]},
                {"has_more":False,"next_cursor":"","events":[{"file":"_air.qo"}]},
            ]
            m = Mock()
            notehub.migrateAirnoteData(pin, deviceId, migrateFunc=m)
            assert m.call_count == 2

def test_migrateAirnoteData_usesLastEventInfoForNextRequest():
    
    pin = "12345"
    deviceId = "dev:864475044207255"

    with patch('notehub.getEventData') as mock_getEventData:
            
            mock_getEventData.side_effect = [
                {"has_more":True,"next_cursor":"abcd","events":[{"file":"_air.qo"}]},
                {"has_more":False,"next_cursor":"","events":[{"file":"_air.qo"}]},
            ]
            m = Mock()
            notehub.migrateAirnoteData(pin, deviceId, migrateFunc=m)
            mock_getEventData.assert_called_with(pin, deviceId, cursor='abcd',limit=50)


def test_migrateAirnoteData_hasMoreFails():
    
    pin = "12345"
    deviceId = "dev:864475044207255"

    with patch('notehub.getEventData') as mock_getEventData:
            
            mock_getEventData.side_effect = [
                {"next_cursor":"defg","events":[{"file":"_air.qo"}]},
            ]
            m = Mock()
            notehub.migrateAirnoteData(pin, deviceId, migrateFunc=m)
            assert m.call_count == 0


def test_migrateAirnoteData_maxCalls():
    
    pin = "12345"
    deviceId = "dev:864475044207255"

    with patch('notehub.getEventData') as mock_getEventData:
            
            mock_getEventData.side_effect = [
                {"has_more":True,"next_cursor":"abcd","events":[{"file":"_air.qo"}]},
                {"has_more":False,"next_cursor":"","events":[{"file":"_air.qo"}]},
            ]
            m = Mock()
            notehub.migrateAirnoteData(pin, deviceId, migrateFunc=m, max_requests=1)
            assert m.call_count == 1


singleEvent = '''{
                "event": "49b8fcf4-c439-4177-a5a4-39bbe3ded4a9",
                "device": "dev:864475044207255",
                "file": "_air.qo",
                "when": 1577841940,
                "body": {
                    "csecs": 484,
                    "sensor": "lnd712",
                    "temperature": 0.01,
                    "voltage": 3.9785156
                },
                "where_lat": 1.516745,
                "where_lon": 103.733556
                }'''
def responseWithOneEventAndNoMoreWaiting():
    r = '''{
            "events":[''' + singleEvent + '''
                
            ],
            "has_more":false,
            "next_cursor":""
        }'''
    return r

# 

def getTestResponse():
    r = '''
    {
        "next_cursor": "ee0f7c1b-754c-4a4b-84fe-07cf3d96ec53",
        "has_more": true,
        "events": [
            {
                "event": "3a531360-577c-447f-b01f-d902014e6a37",
                "device": "dev:864475044207255",
                "file": "_env.dbs",
                "when": 1577841940,
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
                }
           },
            {
                "event": "7c83b38b-bf3d-460d-bbbd-d8e90cdabff4",
                "device": "dev:864475044207255",
                "file": "_air.qo",
                "when": 1577841940,
                "body": {
                    "csecs": 482,
                    "motion": 45,
                    "sensor": "lnd712",
                    "temperature": 0.01,
                    "voltage": 3.9765625
                }
            },
            {
                "event": "3447589a-9724-43fd-92e2-e590fe28e603",
                "device": "dev:864475044207255",
                "file": "_air.qo",
                "when": 1577841940,
                "body": {
                    "csecs": 484,
                    "motion": 31,
                    "sensor": "lnd712",
                    "temperature": 0.01,
                    "voltage": 3.9667969
                }
            },
            {
                "event": "49b8fcf4-c439-4177-a5a4-39bbe3ded4a9",
                "device": "dev:864475044207255",
                "file": "_air.qo",
                "when": 1577841940,
                "body": {
                    "csecs": 484,
                    "sensor": "lnd712",
                    "temperature": 0.01,
                    "voltage": 3.9785156
                }
            }
        ]
    }'''

    return r
