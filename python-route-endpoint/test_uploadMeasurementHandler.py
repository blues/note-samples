from unittest.mock import Mock

import handler
from flask import Flask


def test_uploadMeasurementHandler_constructor():
    m = Mock()
    h = handler.UploadMeasurementHandler(addMeasurementFunc=m)

    assert h._addMeasurement == m


def test_post_standard_notecard_event():
    app = Flask(__name__)
    m = Mock()
    d = standardNotehubEvent
    h = handler.UploadMeasurementHandler(addMeasurementFunc=m)

    with app.test_request_context('/',method='POST',json=d):
        r = h.dispatch_request()
        
        m.assert_called_once_with(d["device"],d["when"],d["body"]["type"],d["body"]["value"],d["body"]["units"])

def test_post_response():
    app = Flask(__name__)
    m = Mock()
    d = standardNotehubEvent
    h = handler.UploadMeasurementHandler(addMeasurementFunc=m)

    with app.test_request_context('/',method='POST',json=d):
        r = h.dispatch_request()
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
    "file": "data.qo",
    "body": {
        "type": "type1",
        "value": 13.3,
        "units":"unit1"
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