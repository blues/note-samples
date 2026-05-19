# note-samples
Notecard and Notehub application samples.
## Content Overview
|Folder|Application Description|
|------|-----------------------|
|[arduino-note-array](arduino-note-array)|Accumulate multiple JSON data elements into a single Notecard note for routing.|
|[esp32-dfu](esp32-dfu)|Arduino/ESP32 sketch demonstrating Notecard-orchestrated host firmware updates (DFU) using the IAP flow: chunked `dfu.get`, OTA partition writes, MD5 validation, and clean error reporting back to Notehub.|
|[python-dfu](python-dfu)|Enable over-the-air updates of Python files executing on a host MCU via Notecard. OTA content packaged in TAR-file. Supports Python and Micropython.|
|[python-large-file-upload](python-large-file-upload)|Upload chunks of a file using Notecard web requests from a Python script.|
|[python-notehub-api](python-notehub-api)|Generate a Python client for the Notehub API from the OpenAPI spec.|
|[python-ota-request-manager](python-ota-request-manager)|Manage and audit fleet-wide DFU (firmware/host) requests across a Notehub project.|
|[python-remote-commands-attn-rpi](python-remote-commands-attn-rpi)|Example Raspberry Pi application in Python that enables users to send "commands" to Raspberry Pi from Notehub. Uses the ATTN pin on Notecard to notify the Raspberry Pi a message is available to be read.|
|[python-route-endpoint](python-route-endpoint)|Example HTTP endpoint that can deploy on Apache to receive data routed from the Notehub cloud service.|
|[python-softap-fix](python-softap-fix)|Repair NOTE-ESP (ESP32 Wi-Fi) Notecards that are missing the assets required to run SoftAP.|
