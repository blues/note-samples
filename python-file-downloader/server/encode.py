
import base64
import math
import zlib

def chunkAsBase64(content, chunk_num=1, chunkSizeInBytes=250):
    contentSize = len(content)

    if(chunkSizeInBytes > contentSize):
        d = base64.b64encode(content)

        return {"data":d.decode("UTF-8"),
                "crc32":zlib.crc32(d), 
                "chunk_num":1,
                "total_chunks":1}

    total_chunks = math.ceil(contentSize/chunkSizeInBytes)

    if(chunk_num > total_chunks):
        raise Exception('Invalid chunk number requested')
    
    
    offset = chunk_num - 1
    startByte = offset * chunkSizeInBytes
    endByte = startByte + chunkSizeInBytes

    chunk = content[startByte:endByte]
    d = base64.b64encode(chunk)
    
    return {"data":d.decode("UTF-8"),
            "crc32":zlib.crc32(d), 
            "chunk_num":chunk_num,
            "total_chunks":total_chunks}


