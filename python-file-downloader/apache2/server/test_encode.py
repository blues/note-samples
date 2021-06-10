import unittest
import base64

from server import encode

class TestFileServer(unittest.TestCase):

    def test_chunkAsBase64_firstChunk2Bytes(self):
        c = b'abcde'
        chunkSize = 2
        chunkNum = 1

        r = encode.chunkAsBase64(c, chunkNum, chunkSizeInBytes=chunkSize)

        self.assertEqual(r["data"],base64.b64encode(b'ab').decode("UTF-8"))
        self.assertEqual(r["chunk_num"], chunkNum)
        self.assertEqual(r["total_chunks"], 3)
        self.assertEqual(r["crc32"], 0x87611f5c)
        

    def test_chunkAsBase64_secondChunk2Bytes(self):
        c = b'abcde'
        chunkSize = 2
        chunkNum = 2

        r = encode.chunkAsBase64(c, chunkNum, chunkSizeInBytes=chunkSize)
        self.assertEqual(r["data"],base64.b64encode(b'cd').decode("UTF-8"))
        self.assertEqual(r["chunk_num"], chunkNum)
        self.assertEqual(r["crc32"], 0x4b668ece)

    def test_chunkAsBase64_InvalidChunkNum(self):
        c = b'abcde'
        chunkSize = 2
        chunkNum = 4

        with self.assertRaises(Exception) as context:
            encode.chunkAsBase64(c, chunkNum, chunkSizeInBytes=chunkSize)

        self.assertTrue('Invalid chunk number requested' in str(context.exception))

    def test_chunkAsBase64_chunkSizeGreaterThanContentSize(self):
        c = b'abcde'
        chunkSize = len(c) + 1
        chunkNum = 1

        r = encode.chunkAsBase64(c, chunkNum, chunkSizeInBytes=chunkSize)
        self.assertEqual(r["data"],base64.b64encode(b'abcde').decode("UTF-8"))
        self.assertEqual(r["chunk_num"], chunkNum)
        self.assertEqual(r["crc32"], 0xfab937d8)





import os
assetPath = "../assets/downloader-example.png"
thisPath = os.path.dirname(__file__)
filename = os.path.join(thisPath, assetPath)
def getTestfileContent():
    with open(filename,'rb') as f:
        s = f.read()
        return(s)

