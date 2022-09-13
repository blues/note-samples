# type: ignore
from typing import Iterable
import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
sys.path.append("src")


import utarfile as utar

import io

  
class TarfileTest(unittest.TestCase):
  
    def test_tarfile_constant_values(self):
        self.assertEqual(utar.BLOCK_LENGTH_BYTES, 512)
        self.assertEqual(utar.HEADER_LENGTH_BYTES, 512)

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_tarfile_init_with_filename_attempts_to_open_file(self,mockOpen):

        fileName = "myfile.tar"
        t = utar.TarFile(fileName)

        mockOpen.assert_called_once_with(fileName, 'rb')
        

    def test_tarfile_init_with_streamObj_internal_streamObj_set(self):
        m = MagicMock(spec=io.BufferedIOBase)

        t = utar.TarFile(m)

        self.assertEqual(t.f, m)

    def test_tarfile_readHeader_hasHeaderInfo_returnsHeaderInfo(self):
        name = "abcd"
        length = 174
        buf = generateTarHeader(name, length)

        f = io.BytesIO(buf)

        t = utar.TarFile(f)
        h = t._readHeader()

        self.assertEqual(h.Name, name)
        self.assertEqual(h.Length, length)
        self.assertEqual(h.Type, utar.Type.FILE)
        self.assertEqual(h.Start, utar.HEADER_LENGTH_BYTES)
        self.assertEqual(h.End, utar.HEADER_LENGTH_BYTES + length)
        self.assertEqual(h.BlockEnd, utar.HEADER_LENGTH_BYTES + utar.BLOCK_LENGTH_BYTES)

    def test_tarfile_readHeader_noInfo_returnsNone(self):
        f = io.BytesIO(generateTarHeader())

        t = utar.TarFile(f)
        h = t._readHeader()

        self.assertIsNone(h)

    def test_tarfile_readHeader_hasFolderInfo_returnsWithTypeDIR(self):
        buf = generateTarHeader("dirname/")
        f = io.BytesIO(buf)
        t = utar.TarFile(f)

        h = t._readHeader()

        self.assertEqual(h.Type, utar.Type.DIR)

    def test_tarfile_readHeader_not_start_of_IOStream_returns_correct_offsets(self):
        buf = generateTarHeader("myName", 17)
        buf = bytearray('\0\0\0', 'utf-8') + buf
        f = io.BytesIO(buf)
        f.seek(3)

        t = utar.TarFile(f)

        h = t._readHeader()
        self.assertEqual(h.Start, 3+utar.HEADER_LENGTH_BYTES)
        self.assertEqual(h.End, 3+utar.HEADER_LENGTH_BYTES + 17)
        self.assertEqual(h.BlockEnd, 3+utar.HEADER_LENGTH_BYTES + utar.BLOCK_LENGTH_BYTES)

    def test_tarfile_next_get_first_item(self):
        content = b'hello world'
        f = io.BytesIO(generateTarItemBin("item1", content))

        t = utar.TarFile(f)
        i = next(t)

        self.assertEqual(i.Name, "item1")
        self.assertEqual(i.Length, len(content))
        self.assertEqual(i.read(), content)

    def test_tarfile_next_get_second_item(self):
        name1 = 'item1'
        content1 = b'abcd'
        name2 = 'item2'
        content2 = b'qrst'

        f = io.BytesIO(generateTarItemBin(name1, content1) + generateTarItemBin(name2, content2))

        t = utar.TarFile(f)
        i1 = next(t)
        i2 = next(t)

        self.assertEqual(i2.Name, name2)
        self.assertEqual(i2.Length, len(content2))
        self.assertEqual(i2.read(), content2)

    def test_tarfile_next_throws_stop_iteration_exception_when_header_is_empty(self):

        f = io.BytesIO(generateTarItemBin())

        t = utar.TarFile(f)

        with self.assertRaises(StopIteration):
            next(t)


    def test_tarfile_iterable_in_for_loop_works_as_expected(self):
        name = 'item'
        content = b'abce'
        tarBytes = generateTarItemBin(name, content) + generateTarItemBin(name, content) + generateTarItemBin()
        f = io.BytesIO(tarBytes)
        t = utar.TarFile(f)

        itemCount = 0
        for i in t:
            self.assertEqual(i.Name, name)
            itemCount += 1

        self.assertEqual(itemCount, 2)

    def test_tarfile_iter_returns_iterable_and_resets_current_item_to_none(self):
        f = io.BytesIO(generateTarItemBin())
        t = utar.TarFile(f)
        t._current_item = utar.TarItem(f, 'name', utar.Type.FILE, 7, 0)
        self.assertIsNotNone(t._current_item)

        m = iter(t)

        self.assertIsInstance(m, Iterable)
        self.assertIsNone(t._current_item)


        

class TarItemTest(unittest.TestCase):

    def test_taritem_constructor_sets_item_properties(self):
        name = "abcd"
        length = 174
        offset = 3
        type = utar.Type.FILE

        f = io.BytesIO()

        i = utar.TarItem(f, name, type, length, offset)
        

        self.assertEqual(i.Name, name)
        self.assertEqual(i.Length, length)
        self.assertEqual(i.Type, type)
        self.assertEqual(i.Start, offset)
        self.assertEqual(i.End, offset + length)
        self.assertEqual(i.BlockEnd, offset + utar.BLOCK_LENGTH_BYTES)

    def test_taritem_read_returns_all_content_starting_from_offset(self):
        headerBytes = b'some-header-bytes\0'
        content = b'this-is-the-content'
        footerBytes = b'\0\0'

        f = io.BytesIO(headerBytes+content+footerBytes)

        i = utar.TarItem(f, "name", utar.Type.FILE, len(content), len(headerBytes))
        c = i.read()

        self.assertEqual(c, content)

    def test_taritem_readinto_populates_buffer_and_returns_bytes_read(self):
        headerBytes = b'some-header-bytes\0'
        content = b'this-is-the-content'
        footerBytes = b'\0\0'

        f = io.BytesIO(headerBytes+content+footerBytes)

        i = utar.TarItem(f, "name", utar.Type.FILE, len(content), len(headerBytes))
        b =  bytearray(len(content))

        s = i.readinto(b)

        self.assertEqual(s, len(content))
        self.assertEqual(b[0:len(content)], content)

    def test_taritem_readinto_buffer_longer_than_available_content_populates_start_of_buffer(self):
        headerBytes = b'some-header-bytes\0'
        content = b'this-is-the-content'
        footerBytes = b'\0\0'

        f = io.BytesIO(headerBytes+content+footerBytes)

        i = utar.TarItem(f, "name", utar.Type.FILE, len(content), len(headerBytes))
        arbitrary_extra_length = 3
        b =  bytearray(len(content) + arbitrary_extra_length)

        s = i.readinto(b)

        self.assertEqual(s, len(content))
        self.assertEqual(b[0:len(content)], content)

    def test_taritem_constructor_passed_dir_type_block_iterator_is_none(self):
        name = "abcd"
        length = 174
        offset = 3
        type = utar.Type.DIR

        f = io.BytesIO()

        i = utar.TarItem(f, name, type, length, offset)
        
        self.assertIsNone(i.Blocks)

    def test_taritem_constructor_passed_file_type_block_iterator_is_tarblock(self):
        name = "abcd"
        length = 174
        offset = 3
        type = utar.Type.FILE

        f = io.BytesIO()

        i = utar.TarItem(f, name, type, length, offset)
        
        self.assertIsInstance(i.Blocks, utar.TarBlock)
        

    




class TestTarBlockIter(unittest.TestCase):
    def test_tarblock_constructor_set_properties(self):
        f = io.BytesIO()
        start = 3
        length = 7

        b = utar.TarBlock(f, start, length)


        self.assertEqual(b._io, f)
        self.assertEqual(b.Start, start)
        self.assertEqual(b.Length, length)
        self.assertEqual(b._current_position, -1)
        self.assertEqual(b._bytes_remaining, length)
        self.assertEqual(b._block_length_bytes, utar.BLOCK_LENGTH_BYTES)

    def test_tarblock_next_no_blocks_left_returns_none(self):
        f = io.BytesIO(b'abc')
        start = 0
        length = 0
        block = utar.TarBlock(f, start, length)

        with self.assertRaises(StopIteration):
            next(block)



    def test_tarblock_next_return_next_available_block(self):
        f = io.BytesIO(b'aabbc\0')
        start = 0
        length = 5
        blockLength = 2

        block = utar.TarBlock(f, start, length)
        block._block_length_bytes = blockLength

        b = next(block)
        self.assertEqual(b._current_position, start)
        self.assertEqual(b._bytes_remaining, length)

        b = next(block)
        self.assertEqual(b._current_position, start + blockLength)
        self.assertEqual(b._bytes_remaining, length - blockLength)

        b = next(block)
        self.assertEqual(b._current_position, start + 2*blockLength)
        self.assertEqual(b._bytes_remaining, length - 2*blockLength)

        with self.assertRaises(StopIteration):
            next(block)

        

    def test_tarblock_iter_returns_iterable_and_resets_position_and_bytes_remaining(self):
        f = io.BytesIO(b'aabbc\0')
        start = 0
        length = 5
        blockLength = 2

        block = utar.TarBlock(f, start, length)
        block._current_position = 13
        block._bytes_remaining = 17
        

        m = iter(block)

        self.assertIsInstance(m, Iterable)
        self.assertEqual(block._current_position, -1)
        self.assertEqual(block._bytes_remaining, length)


    def test_tarblock_read_return_block_content(self):
        content = b'abcdef'
        blockContent = content + b'\0'
        f = io.BytesIO(blockContent)
        start = 0
        length = len(content)
        blockLength = len(blockContent)

        block = utar.TarBlock(f, start, length, blockLength)

        c = block.read()

        self.assertEqual(c, content)


    def test_tarblock_read_content_less_than_block_size(self):
        content = b'abcdef'
        f = io.BytesIO(content)
        start = 0
        length = len(content)
        blockLength = length + 1

        block = utar.TarBlock(f, start, length, blockLength)

        c = block.read()

        self.assertEqual

    def test_tarblock_read_multiple_blocks_returns_content_elements(self):
        content1 = b'abc'
        content2 = b'de'

        self.assertGreaterEqual(len(content1), len(content2), 'Test only valid if second content block is the same size or smaller than the first content block')

        f = io.BytesIO(content1 + content2 + b'\0')
        length = len(content1) + len(content2)
        blockLength = len(content1)
        start = 0

        block = utar.TarBlock(f, start, length, blockLength)

        b = next(block)
        c1 = b.read()

        b = next(block)
        c2 = b.read()

        self.assertEqual(c1, content1)
        self.assertEqual(c2, content2)

    def test_tarblock_read_iostream_pointer_not_at_block_start_byte_still_able_to_read_block(self):
        contentHeader = b'this-is-the-header\0'
        content = b'this-is-the-content'
        contentFooter = b'\0\0'

        blockContent = contentHeader + content + contentFooter

        f = io.BytesIO(blockContent)
        f.seek(0)
        start = len(contentHeader)
        length = len(content)

        block = utar.TarBlock(f, start, length)

        c = block.read()

        self.assertEqual(c, content)

    def test_tarblock_readinto_updates_buffer_with_content_and_returns_size_of_data_read(self):
        content = b'abcdef'
        blockContent = content + b'\0'
        f = io.BytesIO(blockContent)
        start = 0
        length = len(content)
        blockLength = len(blockContent)

        block = utar.TarBlock(f, start, length, blockLength)

        buf = bytearray(len(content))

        s = block.readinto(buf)

        self.assertEqual(s, len(content))
        self.assertEqual(buf, content)

    def test_tarblock_readinto_buffer_longer_than_available_content_populates_start_of_buffer(self):
        content = b'abcdef'
        blockContent = content + b'\0'
        f = io.BytesIO(blockContent)
        start = 0
        length = len(content)
        blockLength = len(blockContent)

        block = utar.TarBlock(f, start, length, blockLength)
        arbitrary_additional_length = 3
        buf = bytearray(len(content) + arbitrary_additional_length)

        s = block.readinto(buf)

        self.assertEqual(s, len(content))
        self.assertEqual(buf[0:len(content)], content)

    def test_tarblock_readinto_multiple_blocks_populates_oversized_buffer_with_content_elements(self):
        content1 = b'abc'
        content2 = b'de'

        self.assertGreaterEqual(len(content1), len(content2), 'Test only valid if second content block is the same size or smaller than the first content block')

        f = io.BytesIO(content1 + content2 + b'\0')
        length = len(content1) + len(content2)
        blockLength = len(content1)
        start = 0

        block = utar.TarBlock(f, start, length, blockLength)

        arbitrary_additional_length = 3
        buf = bytearray(blockLength + arbitrary_additional_length)
        b = next(block)
        s = b.readinto(buf)

        self.assertEqual(s, len(content1))
        self.assertEqual(buf[0:s], content1)

        b = next(block)
        s = b.readinto(buf)

        self.assertEqual(s, len(content2))
        self.assertEqual(buf[0:s], content2)


    def test_tarblock_readinto_iostream_pointer_not_at_block_start_byte_still_able_to_read_block(self):
        contentHeader = b'this-is-the-header\0'
        content = b'this-is-the-content'
        contentFooter = b'\0\0'

        blockContent = contentHeader + content + contentFooter

        f = io.BytesIO(blockContent)
        f.seek(0)
        start = len(contentHeader)
        length = len(content)

        block = utar.TarBlock(f, start, length)

        buf = bytearray(len(blockContent))
        s = block.readinto(buf)

        self.assertEqual(s, len(content))
        self.assertEqual(buf[0:s], content)


class TarExtractorTest(unittest.TestCase):
    def test_tarextractor_constructor_sets_default_properties(self):
        e = utar.TarExtractor()

        self.assertEqual(e.FileName, "")


    @patch("builtins.open", new_callable=mock_open)
    def test__writeTarItemToFile_multipleTarItemBlocks(self, mockOpen):
        e = utar.TarExtractor()

        data = bytearray([1] * (utar.BLOCK_LENGTH_BYTES + 1))
        item = generateTarItem(name = "myfile", content = data)
        

        e._writeTarItemAsFile(item)

        mockOpen.assert_called_once_with("myfile", "wb")
        mockWrite = mockOpen.return_value.__enter__().write
        mockWrite.assert_any_call(data[0:utar.BLOCK_LENGTH_BYTES])
        mockWrite.assert_any_call(data[utar.BLOCK_LENGTH_BYTES:])

    @patch("builtins.open", new_callable=mock_open)
    def test__writeTarItemToFile_userSetRootFolder_fileOpenedInRootFolder(self, mockOpen):
        e = utar.TarExtractor(rootFolder='myrootfolder')

        data = bytearray([1] * (utar.BLOCK_LENGTH_BYTES - 1))
        item = generateTarItem(name = "myfile", content = data)
        

        e._writeTarItemAsFile(item)

        mockOpen.assert_called_once_with("myrootfolder/myfile", "wb")
        

    @patch("os.mkdir")
    def test__writeTarItemAsDir_calls_os_to_make_directory(self, mockMkDir):
        e = utar.TarExtractor()

        i = generateTarItem("myItem", b'hello content')

        e._writeTarItemAsDir(i)

        mockMkDir.assert_called_once_with("myItem")

    @patch("os.mkdir")
    def test__writeTarItemAsDir_userSetRootFolder_mkdirInRootFolder(self, mockMkDir):
        e = utar.TarExtractor(rootFolder="myrootfolder")

        i = generateTarItem("myItem", b'hello content')

        e._writeTarItemAsDir(i)

        mockMkDir.assert_called_once_with("myrootfolder/myItem")

    @patch("builtins.open", new_callable=mock_open)
    def test_extractNext_noPreviousItemExtracted_extractsFirstItem(self, mock_open):
        data = bytearray([1] * (utar.BLOCK_LENGTH_BYTES + 1))
        item = generateTarItemBin(name = "myfile", content = data)
        f = io.BytesIO(item)

        t = utar.TarExtractor(fileName=f)
        # t._writeTarItemAsFile = MagicMock()

        tf = t.extractNext()

        self.assertTrue(tf)
        mock_open.assert_called_once_with("myfile", "wb")

    @patch("builtins.open", new_callable=mock_open)
    def test_extractNext_previousItemExtracted_extractsSecondItem(self, mock_open):
        data = bytearray([1] * (utar.BLOCK_LENGTH_BYTES + 1))
        item1 = generateTarItemBin(name = "myfile1", content = data)
        item2 = generateTarItemBin(name = "myfile2", content = data)
        f = io.BytesIO(item1+item2)

        t = utar.TarExtractor(fileName=f)

        tf = t.extractNext()
        tf = t.extractNext()

        self.assertTrue(tf)
        self.assertEqual(mock_open.call_args_list[1][0], ('myfile2', 'wb'))
        
        
    @patch("builtins.open", new_callable=mock_open)
    def test_extractNext_noMoreItems_returnsFalse(self, mock_open):
        # check using a single valid block
        data = bytearray([1] * (utar.BLOCK_LENGTH_BYTES + 1))
        item = generateTarItemBin(name = "myfile", content = data)
        emptyBlock = generateTarItemBin()
        f = io.BytesIO(item + emptyBlock)

        t = utar.TarExtractor(fileName=f)
        
        t.extractNext()
        tf = t.extractNext()

        self.assertFalse(tf)

        # check using no valid blocks
        f = io.BytesIO(emptyBlock)

        t = utar.TarExtractor(fileName=f)
        
        tf = t.extractNext()

        self.assertFalse(tf)
        
    def test_extractNext_writesDirForDirItem(self):
        
        item1 = generateTarItemBin(name = "mydir1/")

        f = io.BytesIO(item1)

        t = utar.TarExtractor(fileName=f)
        t._mkdir = MagicMock()
        tf = t.extractNext()

        self.assertTrue(tf)
        t._mkdir.assert_called_once_with("mydir1/")

    def test_extractNext_throws_exception_tarfile_not_defined(self):



        t = utar.TarExtractor()

        with self.assertRaisesRegex(Exception, "TAR file not defined"):
            t.extractNext()
            
    
    @patch("builtins.open", new_callable=mock_open)
    def test_openFile_validFileName_opensTarFile(self, mock_open):
        t = utar.TarExtractor()
        self.assertIsNone(t._tarFile)

        t.openFile("myfile.tar")

        self.assertIsInstance(t._tarFile, utar.TarFile)
        mock_open.assert_called_once_with("myfile.tar", "rb")



class ExtractAllTest(unittest.TestCase):
    @patch("os.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_extractAll_generatesFileOrDirForEachItem(self, mockOpen, mockMkdir):
        
        item1 = generateTarItemBin(name = "mydir1/")
        item2 = generateTarItemBin(name = "myfile2", content = b'content 2')
        item3 = generateTarItemBin(name = "myfile3", content = b'content 3')
        emptyBlock = generateTarItemBin()

        f = io.BytesIO(item1 + item2 + item3 + emptyBlock)

        utar.extractAll(f)

        self.assertEqual(mockMkdir.call_args[0][0], "mydir1/")

        args = mockOpen.call_args_list
        firstCallArg = args[0][0][0]
        secondCallArg = args[1][0][0]
        
        self.assertEqual(firstCallArg, "myfile2")
        self.assertEqual(secondCallArg, "myfile3")

    @patch("os.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_extractAll_setUserRootFolder_itemsCreatedInRootFolder(self, mockOpen, mockMkdir):
        
        item1 = generateTarItemBin(name = "mydir1/")
        item2 = generateTarItemBin(name = "myfile2", content = b'content 2')
        emptyBlock = generateTarItemBin()

        f = io.BytesIO(item1 + item2 + emptyBlock)

        utar.extractAll(f, rootFolder="myrootfolder")

        self.assertEqual(mockMkdir.call_args[0][0], "myrootfolder/mydir1/")

        args = mockOpen.call_args_list
        firstCallArg = args[0][0][0]
        
        
        self.assertEqual(firstCallArg, "myrootfolder/myfile2")
        


if __name__ == '__main__':
    unittest.main()



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