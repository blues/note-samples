import json

DEFAULT_SECRETS_FILE_NAME = "secrets.json"
DEFAULT_HUB_HOST = "a.notefile.net"


class AppConfig():
    ProductUID = ""
    HubHost = ""

def loadConfig(fileName = DEFAULT_SECRETS_FILE_NAME) -> AppConfig:
    
    c = AppConfig()

    with open(fileName, 'r') as f:
        info = json.load(f)

        c.ProductUID = info.get('product_uid')
        c.HubHost = info.get('hub_host', DEFAULT_HUB_HOST)

    return c
