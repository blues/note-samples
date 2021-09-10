from unittest.mock import Mock

import handler
from flask import Flask


def test_uploadAlertHandler_constructor():
    m1 = Mock()
    m2 = Mock()
    h = handler.UploadAlertHandler(addAlertFunc=m1, getAlertFunc=m2)

    assert h._addAlert == m1
    assert h._getAlert == m2


def test_post_standard_notecard_event():
    app = Flask(__name__)
    m = Mock()
    d = standardNotehubEvent
    h = handler.UploadAlertHandler(addAlertFunc=m)

    with app.test_request_context('/',method='POST',json=d):
        r = h.dispatch_request()
        
        m.assert_called_once_with(d["device"],d["when"],d["body"]["type"],d["body"]["message"])

def test_post_response():
    app = Flask(__name__)
    m = Mock()
    d = standardNotehubEvent
    h = handler.UploadAlertHandler(addAlertFunc=m)

    with app.test_request_context('/',method='POST',json=d):
        r = h.dispatch_request()
        assert r[1] == 200


def test_get_response():
    app = Flask(__name__)
    m = Mock()
    e = [{"deviceId":"abc","timestamp":"1234","type":"somealert","message":"a message"}]
    m.return_value = e

    h = handler.UploadAlertHandler(getAlertFunc = m)

    with app.test_request_context('/',method='GET'):
        r = h.dispatch_request()
        assert r[0] == e
        assert r[1] == 200








standardNotehubEvent = {
    "event": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "session": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "best_id": "dev:xxxxxxxxxxxxxxx",
    "device": "dev:xxxxxxxxxxxxxxx",
    "product": "product:com.email.myname:uid",
    "received": 1627495495.552799,
    "routed": 1627495495,
    "req": "note.add",
    "when": 1627495494,
    "file": "alerts.qo",
    "body": {
        "type": "alerttype1",
        "message":"message 1"
    },
    "best_location_type": "tower",
    "best_lat": 47.0001,
    "best_lon": -73.0001,
    "best_location": "Somewhere MA",
    "best_country": "US",
    "best_timezone": "America/New_York",
    "tower_when": 1627494970,
    "tower_lat": 47.0001,
    "tower_lon": -73.0001,
    "tower_country": "US",
    "tower_location": "Somewhere MA",
    "tower_timezone": "America/New_York",
    "tower_id": "310,410,1049,15864835",
}