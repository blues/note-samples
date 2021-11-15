class AppConfig:
    ProductUID  = 'com.my.product.uid'
    HubHost     = "a.notefile.net"
    EnableDebug = False
    PortType    = "i2c"
    PortName    = "/dev/i2c-1"
    BaudRate    = 9600
    

import os


def GetConfig() -> AppConfig:
    c = AppConfig()
    c.ProductUID  =     os.getenv("PRODUCT_UID", c.ProductUID)
    c.HubHost     =     os.getenv("HUB_HOST", c.HubHost) 
    c.PortName    =     os.getenv("PORT_NAME", c.PortName)
    c.BaudRate    = int(os.getenv("BAUD_RATE", str(c.BaudRate)))
    c.EnableDebug =     os.getenv("DEBUG",     str(c.EnableDebug)).lower() in ('true', '1', 't', 'on')

    portType = os.getenv("PORT_TYPE")
    if portType and portType.lower() in ('uart', 'usb'):
        c.PortType = 'uart'
    
    return c