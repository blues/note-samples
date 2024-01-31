# Python Notehub API

Generate the Python Notehub API from the API spec.

## Installing the Generator Tool

```bash
npm install @openapitools/openapi-generator-cli -g
```

## Download the latest OpenAPI Spec

Linux

```bash
wget https://github.com/blues/notehub-js/raw/main/openapi.yaml
```

Windows

```powershell
Invoke-WebRequest -Uri https://github.com/blues/notehub-js/raw/main/openapi.yaml -OutFile ./openapi.yaml
```

## Repair API Spec

The `serial_number` field of the `Device` model is listed as a required element.  The Notehub API will not return a device serial number if one is not populated for the device in Notehub.  

Remove the line containing `- serial number` under the list of required fields in the device object. (Approximately line 2709)

## Execute Python API Generation

```bash
openapi-generator-cli generate -i openapi.yaml -g python --additional-properties packageName=notehub_api -o ./src
```

## Quick Start for Using Resulting API

Use the following system commands to migrate to the correct folder and install the dependencies

```bash
cd src
python -m venv .venv
pip install -r requirements.txt
```

Once the dependencies are installed, you can execute an example script

```python


import time
import notehub_api
from notehub_api.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.notefile.net
# See configuration.py for a list of all supported configuration parameters.
configuration = notehub_api.Configuration(
    host = "https://api.notefile.net"  #
)
token = 'api-token-will-go-here'
with notehub_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = notehub_api.AuthorizationApi(api_client)
    login_request = {"username":"name@example.com","password":"test-password"} # LoginRequest | 
    api_response = api_instance.login(login_request)
    token = api_response.session_token

configuration.api_key['api_key'] = token

# Enter a context with an instance of the API client
with notehub_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    device_api_instance = notehub_api.DevicesApi(api_client)
    env_api_instance = notehub_api.EnvironmentVariablesApi(api_client)
    project_uid = 'notehub-project-uid-goes-here' # str | 
    page_size = 50 # int |  (optional) (default to 50)
    page_num = 1 # int |  (optional) (default to 1)

    #api_response = api_instance.get_project_devices(project_uid, page_size=page_size, page_num=page_num)
    #api_response = env_api_instance.get_device_environment_variables(project_uid, 'dev:864475040058462')
    api_response = device_api_instance.get_device(project_uid, 'dev:xxxxxxxxxxxxxxxx')
    print("The response of DevicesApi->get_project_devices:\n")
    pprint(api_response)
```
