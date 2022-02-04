import json
import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
sys.path.append("..")


import src.config as config

import io

  
class ConfigTest(unittest.TestCase):
  
    def test_config_constant_values(self):
        self.assertEqual(config.DEFAULT_SECRETS_FILE_NAME, "secrets.json")
        self.assertEqual(config.DEFAULT_HUB_HOST, "a.notefile.net")
        self.assertEqual(config.DEFAULT_PORT_TYPE, "uart")
        self.assertEqual(config.DEFAULT_DEBUG_FLAG, True)
        self.assertEqual(config.DEFAULT_PORT_ID, 0)
        self.assertEqual(config.DEFAULT_PORT_BAUDRATE, 9600)

    @patch("builtins.open", new_callable=mock_open, read_data = "{}")
    def test_config_loadConfig_noInputArg_usesDefaultFileName(self,mockOpen):

        
        c = config.loadConfig()

        mockOpen.assert_called_once_with(config.DEFAULT_SECRETS_FILE_NAME, 'r')

    @patch("builtins.open", new_callable=mock_open, read_data = "{}")
    def test_config_loadConfig_fileNameArg_usesFileNameArg(self,mockOpen):

        fileName = "testName.json"
        c = config.loadConfig(fileName = fileName)

        mockOpen.assert_called_once_with(fileName, 'r')

    
    def test_config_loadConfig_returnsConfigFromFile(self):

        data = {
                "product_uid":"dummy_product_uid", 
                "hub_host":"test-host.net",
                "port_type": "i2c", 
                "port_id": 17,
                "port_baudrate": 115200, 
                "debug": False}

        with patch("builtins.open", mock_open(read_data=json.dumps(data)), create=True) as mockOpen:
    

            c = config.loadConfig()

            self.assertEqual(c.ProductUID, data["product_uid"])
            self.assertEqual(c.HubHost, data["hub_host"])
            self.assertEqual(c.PortType, data["port_type"])
            self.assertEqual(c.PortID, data["port_id"])
            self.assertEqual(c.PortBaudRate, data["port_baudrate"])
            self.assertEqual(c.Debug, data["debug"])

    def test_config_loadConfig_no_json_content_returnDefaults(self):

        with patch("builtins.open", mock_open(read_data="{}"), create=True) as mockOpen:
    

            c = config.loadConfig()

            self.assertIsNone(c.ProductUID)
            self.assertEqual(c.HubHost,config.DEFAULT_HUB_HOST)
            self.assertEqual(c.PortType, config.DEFAULT_PORT_TYPE)
            self.assertEqual(c.Debug, config.DEFAULT_DEBUG_FLAG)
            self.assertEqual(c.PortID, config.DEFAULT_PORT_ID)
            self.assertEqual(c.PortBaudRate, config.DEFAULT_PORT_BAUDRATE)
    
    
    def test_config_loadConfig_valid_port_types_all_work(self):

        validTypes = ['UART', 'uart', 'USB', 'usb', 'I2C', 'i2c']

        for t in validTypes:
            with patch("builtins.open", mock_open(read_data=json.dumps({"port_type":t})), create=True) as mockOpen:
                c = config.loadConfig()
                self.assertEqual(c.PortType, t.lower())
                
        

    def test_config_loadConfig_invalid_porttype_raises_exception(self):
        with patch("builtins.open", mock_open(read_data=json.dumps({"port_type":"invalid_type"})), create=True) as mockOpen:
            self.assertRaises(Exception, config.loadConfig)



    def test_config_loadConfig_valid_baudrates_all_work(self):

        validRates = [9600, 115200]

        for r in validRates:
            with patch("builtins.open", mock_open(read_data=json.dumps({"port_baudrate":r})), create=True) as mockOpen:
                c = config.loadConfig()
                self.assertEqual(c.PortBaudRate, r)
                
        

    def test_config_loadConfig_invalid_baudrate_raises_exception(self):
        with patch("builtins.open", mock_open(read_data=json.dumps({"port_baudrate":3})), create=True) as mockOpen:
                self.assertRaises(Exception, config.loadConfig)