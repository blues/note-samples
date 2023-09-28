import serial
import notecard
import logging
import configargparse
import time
import binascii


# Define default options
DEFAULT_PORT_ID = "COM4"
DEFAULT_PORT_BAUDRATE = 9600
DEFAULT_DEBUG_TRANSACTIONS = True
DEFAULT_WAIT_FOR_CONNECTION = True
DEFAULT_LOG_FOLDER = './'
DEFAULT_ROUTE_NAME = "ping"
DEFAULT_HUB_MODE = "continuous"
DEFAULT_CHUNK_SIZE_BYTES = 1024
DEFAULT_WEB_REQUEST_TIMEOUT = 30

## Function to parse command-line arguments
def parseCommandLineArgs():

    DESCRIPTION = """Example for uploading larger files and data to the cloud
    
    """


    p = configargparse.ArgumentParser(description=DESCRIPTION,
                                      default_config_files=['./config.txt'])

    p.add("-u","--product-uid", help="Notehub Product UID (com.company.name.project)", env_var="PRODUCT_UID", required=True)
    p.add("-p", "--port", help="Serial port identifier for serial port connected to Notecard", default=DEFAULT_PORT_ID)
    p.add("-b", "--baudrate", help="Serial port baudrate (bps)", default=DEFAULT_PORT_BAUDRATE, type = int)
    p.add("-r", "--route", help="Name of route Notecard web request transactions will use", default=DEFAULT_ROUTE_NAME)
    p.add("-d", "--debug-transactions", help="Display Notecard transactions", default=DEFAULT_DEBUG_TRANSACTIONS, type=lambda x:bool(strtobool(x)),nargs='?',const=True)
    p.add("-lf", "--log-folder", help="Directory where log files are stored", default=DEFAULT_LOG_FOLDER, env_var="LOG_FOLDER")
    p.add("-f", "--file", help="File to use as data source for transfer", required=True)
    p.add("-w", "--wait-for-connection", help="Wait until Notecard is connected to Notehub", default=DEFAULT_WAIT_FOR_CONNECTION, type=lambda x:bool(strtobool(x)),nargs='?',const=True)
    p.add("-m", "--mode", help="Notecard connection mode to Notehub (continuous, periodic, minimum)", default=DEFAULT_HUB_MODE)
    p.add("-s", "--chunk-size", help="Size of file chunk to transfer in bytes", default=DEFAULT_CHUNK_SIZE_BYTES, type=int)
    p.add("-t", "--timeout", help="Web request timeout in seconds", default=DEFAULT_WEB_REQUEST_TIMEOUT, type=int)

    opts = p.parse_args()
    return opts

## Get options
opts = parseCommandLineArgs()
use_temp_continuous = opts.mode != 'continuous'

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


if (opts.file):
    sendFileBytes(opts.file)
else:
    logging.warning("No file selected to parse and send bytes")


if use_temp_continuous:
    unsetTempContinuousMode()
