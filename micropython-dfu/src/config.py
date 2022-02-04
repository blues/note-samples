class PortType():
    UART = "uart"
    USB = "usb"
    I2C = "i2c"

import json

DEFAULT_SECRETS_FILE_NAME = "secrets.json"
DEFAULT_HUB_HOST = "a.notefile.net"
DEFAULT_PORT_TYPE = PortType.UART
DEFAULT_PORT_ID = 0
DEFAULT_PORT_BAUDRATE = 9600

DEFAULT_DEBUG_FLAG = True



class AppConfig():
    ProductUID = ""
    HubHost  = DEFAULT_HUB_HOST
    PortType = DEFAULT_PORT_TYPE
    PortID   = DEFAULT_PORT_ID
    PortBaudRate = DEFAULT_PORT_BAUDRATE
    Debug    = DEFAULT_DEBUG_FLAG


def loadConfig(fileName = DEFAULT_SECRETS_FILE_NAME) -> AppConfig:
    
    validPortTypes = [PortType.UART, PortType.USB, PortType.I2C]
    validBaudRates = [9600, 115200]

    c = AppConfig()

    with open(fileName, 'r') as f:
        info = json.load(f)

        c.ProductUID   = info.get('product_uid')
        c.HubHost      = info.get('hub_host', DEFAULT_HUB_HOST)
        c.PortType     = info.get('port_type', DEFAULT_PORT_TYPE).lower()
        if c.PortType not in validPortTypes:
            raise Exception(f"Port Type must be a member of {validPortTypes} ")
        
        c.PortID       = info.get('port_id', DEFAULT_PORT_ID)
        c.PortBaudRate = info.get('port_baudrate', DEFAULT_PORT_BAUDRATE)
        if c.PortBaudRate not in validBaudRates:
            raise Exception(f"Port Baud Rate must be a member of {validBaudRates} ")
            
        c.Debug        = info.get('debug', DEFAULT_DEBUG_FLAG)

    return c
