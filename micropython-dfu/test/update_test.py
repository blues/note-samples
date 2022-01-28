
import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import io
sys.path.append("..")
sys.path.append("../src")


import src.update as update
import src.utarfile as utar


  
class UpdateManagerTest(unittest.TestCase):
  
    def test_update_constant_values(self):
        pass


    def test_constructor_inputArgs_populate_manager_attributes(self):
        c = MagicMock()
        m = update.UpdateManager(card=c)

        self.assertEqual(m._card, c)

        s = MagicMock()
        m = update.UpdateManager(statusUpdater = s)

        self.assertEqual(m._statusUpdater, s)

    def test_gather_noUpdateAvailable_returns_None_provides_status_message(self):
        card = MagicMock()
        s = MagicMock()
        m = update.UpdateManager(card=card, statusUpdater=s)
        m._dfu = MagicMock()
        m._dfu.isUpdateAvailable.return_value = False

        f = m.gather()

        self.assertEqual(f, "")
        s.assert_called_once_with("No update available", None)

    @patch("builtins.open", new_callable=mock_open)
    def test_gather_updateAvailable_copiesImageToFile_providesStatusMessages(self, mockOpen):
        card = MagicMock()
        s = MagicMock()
        m = update.UpdateManager(card=card, statusUpdater=s)
        m._dfu = MagicMock()
        m._dfu.isUpdateAvailable.return_value = True
        fileName = "myfile.tar"
        m._dfu.getUpdateInfo.return_value = {"source": fileName}

        
        f = m.gather()

        mockOpen.assert_called_once_with(fileName, "wb")
        args = m._dfu.copyImageToWriter.call_args
        self.assertEqual(args[0][0], card)
        
        p = args[1]['progressUpdater']
        percentComplete = 13
        p(percentComplete)
        s.assert_called_with("Migrating", percentComplete)

        s.assert_any_call("Successful copy of update", None)

        m._dfu.setUpdateDone.assert_called_once_with(card, 'copied image to file')

        self.assertEqual(f, fileName)

    @patch("builtins.open", new_callable=mock_open)
    def test_gather_update_file_open_fails(self, mockOpen):
        card = MagicMock()
        s = MagicMock()
        m = update.UpdateManager(card=card, statusUpdater=s)
        m._dfu = MagicMock()
        m._dfu.isUpdateAvailable.return_value = True
        fileName = "myfile.tar"
        m._dfu.getUpdateInfo.return_value = {"source": fileName}

        mockOpen.side_effect = FileExistsError


        f = m.gather()
        self.assertEqual(f, "")
        s.assert_any_call("Failed to migrate update", None)

        m._dfu.setUpdateError.assert_called_with(card, "failed to copy image to file")

        
    @patch("builtins.open", new_callable=mock_open)
    def test__writeTarItemToFile_multipleTarItemBlocks(self, mockOpen):
        card = MagicMock()
        m = update.UpdateManager(card=card)

        data = bytearray([1] * (utar.BLOCK_LENGTH_BYTES + 1))
        item = generateTarItem(name = "myfile", content = data)

        m._writeTarItemToFile(item)

        mockOpen.assert_called_once_with("myfile", "wb")
        mockWrite = mockOpen.return_value.__enter__().write
        mockWrite.assert_any_call(data[0:utar.BLOCK_LENGTH_BYTES])
        mockWrite.assert_any_call(data[utar.BLOCK_LENGTH_BYTES:])
        


    @patch("builtins.open", new_callable=mock_open)
    def test_extract_generatesFileForEachItem(self, mockOpen):
        card = MagicMock()
        m = update.UpdateManager(card=card)

        
        item1 = generateTarItemBin(name = "mydir1/")
        item2 = generateTarItemBin(name = "myfile2", content = b'content 2')
        item3 = generateTarItemBin(name = "myfile3", content = b'content 3')
        emptyBlock = generateTarItemBin()

        f = io.BytesIO(item1 + item2 + item3 + emptyBlock)
        mockOpen.return_value = f

        m._writeTarItemToFile = MagicMock()
        m._writeTarItemAsDir = MagicMock()

        m.extract("myfile")

        mockOpen.assert_called_once_with("myfile", "rb")
        self.assertEqual(m._writeTarItemAsDir.call_args[0][0].Name, "mydir1/")

        args = m._writeTarItemToFile.call_args_list
        firstCallArg = args[0][0][0]
        secondCallArg = args[1][0][0]
        
        self.assertEqual(firstCallArg.Name, "myfile2")
        self.assertEqual(secondCallArg.Name, "myfile3")
        
        
    @patch("os.mkdir")
    def test__writeTarItemAsDir_calls_os_to_make_directory(self, mockMkDir):
        card = MagicMock()
        m = update.UpdateManager(card = card)

        i = generateTarItem("myItem", b'hello content')

        m._writeTarItemAsDir(i)

        mockMkDir.assert_called_once_with("myItem")

        



def generateTarHeader(name="", length=0):
    buf = bytearray(512)
    buf[0:len(name)] = bytearray(name,'utf-8')


    b = bytes(oct(length)[2:],'utf-8')

    buf[124:135] = bytearray(b).rjust(11,b'0')

    return buf


def generateTarItemBin(name="", content=b''):
    length = len(content)
    s = utar.BLOCK_LENGTH_BYTES
    bufferLength =  s * (length//s + int((length % s) > 0))
    buf = bytearray(bufferLength)
    buf[0:length] = content
    header = generateTarHeader(name, length)
    return header + buf

def generateTarItem(name="", content=b''):
    bin = generateTarItemBin(name=name, content = content)
    
    f = io.BytesIO(bin)
    type = utar.Type.DIR if name[-1] == '/' else utar.Type.FILE
    i = utar.TarItem(f, name, type, len(content), utar.HEADER_LENGTH_BYTES)
    return i


    


    # @patch("builtins.open", new_callable=mock_open, read_data = "{}")
    # def test_config_loadConfig_fileNameArg_usesFileNameArg(self,mockOpen):

    #     fileName = "testName.json"
    #     c = config.loadConfig(fileName = fileName)

    #     mockOpen.assert_called_once_with(fileName, 'r')

    
    # def test_config_loadConfig_returnsConfigFromFile(self):

    #     data = {"product_uid":"dummy_product_uid", "hub_host":"test-host.net"}

    #     with patch("builtins.open", mock_open(read_data=json.dumps(data)), create=True) as mockOpen:
    

    #         c = config.loadConfig()

    #         self.assertEqual(c.ProductUID, data["product_uid"])
    #         self.assertEqual(c.HubHost, data["hub_host"])

    # def test_config_loadConfig_no_json_content_returnDefaults(self):

    #     with patch("builtins.open", mock_open(read_data="{}"), create=True) as mockOpen:
    

    #         c = config.loadConfig()

    #         self.assertIsNone(c.ProductUID)
    #         self.assertEqual(c.HubHost,config.DEFAULT_HUB_HOST)

    
        
        
