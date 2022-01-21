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

        data = {"product_uid":"dummy_product_uid", "hub_host":"test-host.net"}

        with patch("builtins.open", mock_open(read_data=json.dumps(data)), create=True) as mockOpen:
    

            c = config.loadConfig()

            self.assertEqual(c.ProductUID, data["product_uid"])
            self.assertEqual(c.HubHost, data["hub_host"])

    def test_config_loadConfig_no_json_content_returnDefaults(self):

        with patch("builtins.open", mock_open(read_data="{}"), create=True) as mockOpen:
    

            c = config.loadConfig()

            self.assertIsNone(c.ProductUID)
            self.assertEqual(c.HubHost,config.DEFAULT_HUB_HOST)

    
        
        
