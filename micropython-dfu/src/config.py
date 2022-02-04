class PortType():
    UART = "uart"
    USB = "uart"
    I2C = "i2c"

import json

DEFAULT_SECRETS_FILE_NAME = "secrets.json"
DEFAULT_HUB_HOST = "a.notefile.net"
DEFAULT_PORT_TYPE = PortType.UART
DEFAULT_PORT_NAME = ""
DEFAULT_PORT_BAUDRATE = 9600

DEFAULT_DEBUG_FLAG = True



class AppConfig():
    ProductUID = ""
    HubHost  = ""
    PortType = DEFAULT_PORT_TYPE
    PortName = DEFAULT_PORT_NAME
    PortBaudRate = DEFAULT_PORT_BAUDRATE
    Debug    = DEFAULT_DEBUG_FLAG


def loadConfig(fileName = DEFAULT_SECRETS_FILE_NAME) -> AppConfig:
    
    c = AppConfig()

    with open(fileName, 'r') as f:
        info = json.load(f)

        c.ProductUID = info.get('product_uid')
        c.HubHost = info.get('hub_host', DEFAULT_HUB_HOST)

    return c
