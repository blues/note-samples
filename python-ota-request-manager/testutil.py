



def standardEnvironmentVars(environmentVars={}):
    
    e = {n:str(v) for n,v in environmentVars.items()}
    
    return {
        "environment_variables": e,
        "environment_variables_env_default": {}
        }



def standardDeviceJSON(parameters={}):
    json = {
            "uid":"dev:000000000000000",
            "serial_number":"",
            "provisioned":"2021-02-11T02:37:16Z",
            "last_activity":"2021-05-11T19:37:08Z",
            "contact": None,
            "product_uid":"product:com.your-company.your-name:project",
            "fleet_uids":["fleet:00000000-0000-0000-0000-000000000000"],
            "tower_info":{
            "mcc":310,
            "mnc":410,
            "lac":12345,
            "cell_id":12345678
            },
            "tower_location":{
            "when":"2021-05-11T19:34:23Z",
            "name":"Cassville MO",
            "country":"US",
            "timezone":"America/Chicago",
            "latitude":36.665537500000006,
            "longitude":-93.850109375
            },
            "gps_location":{
            "same properties as tower_location"
            },
            "triangulated_location":{
            "same properties as tower_location"
            },
            "voltage":5.15,
            "temperature":23.75,
            "dfu":{
            "card":{
                "type":"card",
                "mode":"idle",
                "updated":1632938485,
                "version":"{\"org\":\"Blues Wireless\",\"product\":\"Notecard\",\"version\":\"notecard-1.5.6\",\"ver_major\":1,\"ver_minor\":5,\"ver_patch\":6,\"ver_build\":13695,\"built\":\"Sep 13 2021 15:37:30\"}"
            },
            "user":{
                "type":"user",
                "mode":"idle",
                "updated":1632938486
            }
            },
            "sku":"NOTE-WBNA-500"
        }
    
    for p in parameters:
        json[p] = parameters[p]

    return json
