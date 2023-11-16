import serial
import notecard
import logging
import configargparse
import time
import binascii


# Define default options
DEFAULT_PORT_TYPE = "serial"
DEFAULT_SERIAL_PORT_ID = "COM4"
DEFAULT_I2C_PORT_ID = "/dev/i2c-1"
DEFAULT_PORT_BAUDRATE = 9600
DEFAULT_DEBUG_TRANSACTIONS = True
DEFAULT_WAIT_FOR_CONNECTION = True
DEFAULT_LOG_FOLDER = './'
DEFAULT_ROUTE_NAME = "ping"
DEFAULT_HUB_MODE = "continuous"
DEFAULT_CHUNK_SIZE_BYTES = 1024
DEFAULT_WEB_REQUEST_TIMEOUT = 30
DEFAULT_MEASURE_TRANSFER_TIME = True

def str2bool(v):
    return v.lower() in ["true", "t", "1", "on", "yes", "y"]

## Function to parse command-line arguments
def parseCommandLineArgs():

    DESCRIPTION = """Example for uploading larger files and data to the cloud
    
    """


    p = configargparse.ArgumentParser(description=DESCRIPTION,
                                      default_config_files=['./config.txt'])

    p.add("-u","--product-uid", help="Notehub Product UID (com.company.name.project)", env_var="PRODUCT_UID", required=True)
    p.add("-p", "--port", help="Serial port identifier for port connected to Notecard")
    p.add("-b", "--baudrate", help="Serial port baudrate (bps)", default=DEFAULT_PORT_BAUDRATE, type = int)
    p.add("-r", "--route", help="Name of route Notecard web request transactions will use", default=DEFAULT_ROUTE_NAME)
    p.add("-d", "--debug-transactions", help="Display Notecard transactions", default=DEFAULT_DEBUG_TRANSACTIONS, type=lambda x:bool(str2bool(x)),nargs='?',const=True)
    p.add("-lf", "--log-folder", help="Directory where log files are stored", default=DEFAULT_LOG_FOLDER, env_var="LOG_FOLDER")
    p.add("-f", "--file", help="File to use as data source for transfer")
    p.add("-w", "--wait-for-connection", help="Wait until Notecard is connected to Notehub", default=DEFAULT_WAIT_FOR_CONNECTION, type=lambda x:bool(str2bool(x)),nargs='?',const=True)
    p.add("-m", "--mode", help="Notecard connection mode to Notehub (continuous, periodic, minimum)", default=DEFAULT_HUB_MODE)
    p.add("-s", "--chunk-size", help="Size of file chunk to transfer in bytes", default=DEFAULT_CHUNK_SIZE_BYTES, type=int)
    p.add("-t", "--timeout", help="Web request timeout in seconds", default=DEFAULT_WEB_REQUEST_TIMEOUT, type=int)
    p.add("-e", "--measure-elapsed-time", help="Measure how long the file transfer process takes", default=DEFAULT_MEASURE_TRANSFER_TIME, type=lambda x:bool(str2bool(x)),nargs='?',const=True )
    p.add("-n", "--port-type", help="Select Serial or I2C port type", default=DEFAULT_PORT_TYPE)
    p.add("-z", "--test-size", help="Size in Bytes of test data to use", default=0, type=int);

    opts = p.parse_args()
    return opts

## Get options
opts = parseCommandLineArgs()

use_temp_continuous = opts.mode != 'continuous'
using_i2c = opts.port_type.lower() == "i2c"
if opts.port is None:
    opts.port = DEFAULT_I2C_PORT_ID if using_i2c else DEFAULT_SERIAL_PORT_ID

if opts.file == None and opts.test_size == 0:
    raise(Exception("Must provide either a file or a size of a test in bytes"))

if opts.file != None and opts.test_size != 0:
    raise(Exception("Cannot provide both a file and a size of a test in bytes"))

using_file = opts.file != None

## Configure logging
logFolder = opts.log_folder.rstrip("/\\")
logLevel = logging.DEBUG if opts.debug_transactions else logging.INFO
logging.basicConfig(
    level=logLevel,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f'{logFolder}/{time.strftime("%Y%m%d-%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logging.info(opts)

## Connect to Notecard
port = None
card = None
if using_i2c:
    # Use python-periphery on a Linux desktop or Raspberry Pi
    from periphery import I2C
    port = I2C(opts.port)
    card = notecard.OpenI2C(port, debug=opts.debug_transactions)
else: 
    port = serial.Serial(opts.port, baudrate=opts.baudrate)
    card = notecard.OpenSerial(port, debug=opts.debug_transactions)

## Notecard Request Method
def sendRequest(req, args=None, ignoreErrors = [], errRaisesException=True):
    if isinstance(req,str):
        req = {"req":req}

    if args:
        req = dict(req, **args)

    logging.debug(req)
    rsp = card.Transaction(req)
    logging.debug(rsp)
    if errRaisesException and 'err' in rsp:
        if any(s in rsp['err'] for s in ignoreErrors):
            return rsp

        raise Exception("Notecard Transaction Error: " + rsp['err'])

    return rsp



## Log Notecard Info
rsp = sendRequest("card.version")
logging.info(f"NOTECARD INFO Device: {rsp['device']} SKU: {rsp['sku']} Firmware Version: {rsp['version']}")

## Configure Notehub Connection
hubConfig = {
    "mode": opts.mode.lower(),
    "sync":True, 
    "product":opts.product_uid
    }

sendRequest("hub.set", hubConfig)
logging.info(f"HUB INFO  ProductUID: {hubConfig['product']}  Sync: {hubConfig['sync']}")


## Configure Baseline Web Request
webReq = {"req":"web.post",
    "payload":"",
    "seconds": opts.timeout,
    "route":opts.route,
    "offset":0,
    "total":0
    }

## Generate and Perform Web Request from Chunk of file Bytes
def writeWebReqChunk(payload, offset, total):
    webReq['payload'] = str(binascii.b2a_base64(bytes(payload))[:-1], 'utf-8')
    webReq['offset'] = offset
    webReq['total'] = total
    rsp = sendRequest(webReq)

    if rsp.get("result", 300) >= 300:
        msg = rsp.get('body', {}).get('err', 'unknown')
        raise Exception("Web Request Error: " + msg)


def sendDataBytes(sizeOfTestData, chunk_size):
    data = bytearray([7]*int(sizeOfTestData))

    totalBytes = len(data)
    numBytes = 0
    while numBytes <= totalBytes:
        e = min(numBytes + chunk_size, totalBytes)
        try:
            writeWebReqChunk(data[numBytes:e], numBytes, totalBytes)
        except:
            break

        numBytes = e


def sendFileBytes(filename):
    logging.info(f"Using file: {filename}")
    
    with open(filename, 'rb') as p:
        p.seek(0, 2)
        totalBytes = p.tell()
        p.seek(0,0)

        keepReading = True
        s = 0
        numBytes = 0
        while keepReading:
            payload = p.read(opts.chunk_size)
            numPayloadBytes = len(payload) 
            keepReading = numPayloadBytes >=opts.chunk_size
            
            
            try:
                writeWebReqChunk(payload, numBytes, totalBytes)
            except:
                break

            
            numBytes += numPayloadBytes
             
    
    logging.info(f"Payload Size: {numBytes/1024} KB.")
            

def waitForConnection():
    req = {"req":"hub.status"}
    isConnected=False
    while not isConnected:
        rsp = sendRequest(req)
        isConnected =  rsp.get('connected', False)
        time.sleep(1)

def setTempContinuousMode():
    timeoutSecs = 3600
    req = {"req":"hub.set", "on":True, "seconds":timeoutSecs}
    sendRequest(req)

def unsetTempContinuousMode():
    req = {"req":"hub.set", "off":True}
    sendRequest(req)


if use_temp_continuous:
    setTempContinuousMode()

if opts.wait_for_connection or use_temp_continuous:
    logging.info(f"Waiting for Notehub connection")
    waitForConnection()

startTime = 0
if using_file:
    startTime = time.time()
    sendFileBytes(opts.file)
    endTime = time.time()
else:
    startTime = time.time()
    sendFileBytes(opts.test_size, opts.chunk_size)
    endTime = time.time()


if use_temp_continuous:
    unsetTempContinuousMode()

if opts.measure_elapsed_time:
    logging.info(f"Elapsed time sending file: {endTime-startTime} seconds")
