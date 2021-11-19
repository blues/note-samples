
import config
from unittest.mock import patch

def test_GetConfig_Defaults():
    c = config.GetConfig()

    assert c.ProductUID == 'com.my.product.uid'
    assert c.HubHost == "a.notefile.net"
    assert c.PortType == "i2c"
    assert c.PortName == "/dev/i2c-1"
    assert c.BaudRate == 9600
    assert not c.EnableDebug


def test_GetConfig_setAllEnvironmentVars():
    e = {"PRODUCT_UID": 'dummy_product_uid',
         "PORT_TYPE": 'uart',
         "PORT_NAME": "COM6",
         "BAUD_RATE": "115200",
         "HUB_HOST": "a.b.c",
         "DEBUG": "true"}

    with patch.dict('os.environ', e, clear=True):
        c = config.GetConfig()
        assert c.ProductUID == 'dummy_product_uid'
        assert c.HubHost == "a.b.c"
        assert c.PortType == "uart"
        assert c.PortName == "COM6"
        assert c.BaudRate == 115200
        assert c.EnableDebug

def test_GetConfig_PortType():
    # These options result in port type of uart
    UartOpts = ["uart", "usb", "UART", "USB"]
    for uart in UartOpts:
        with patch.dict('os.environ', {"PORT_TYPE":uart}):
            c = config.GetConfig()
            assert c.PortType == "uart"

    # Anything not listed for UART options results in I2C
    AnythingElse = ["i2c", "I2C", "blah"]

    for i2c in AnythingElse:
        with patch.dict('os.environ', {"PORT_TYPE": i2c}):
            c = config.GetConfig()
            assert c.PortType == "i2c"

def test_GetConfig_EnableDebug():
    validEnableOpts = ["TRUE", "true", "T", "t", "1", "on", "ON"]
    for opt in validEnableOpts:
        with patch.dict('os.environ', {"DEBUG": opt}):
            c = config.GetConfig()
            assert c.EnableDebug