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
DEFAULT_LOG_FOLDER = './'
DEFAULT_ROUTE_NAME = "ping"

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

    opts = p.parse_args()
    return opts

## Get options
opts = parseCommandLineArgs()
print(opts)

## Configure logging
logFolder = opts.log_folder.rstrip("/\\")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f'{logFolder}/{time.strftime("%Y%m%d-%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

## Connect to Notecard
port = serial.Serial(opts.port, baudrate=opts.baudrate)
card = notecard.OpenSerial(port, debug=opts.debug_transactions)

## Notecard Request Method
def sendRequest(req, args=None, ignoreErrors = [], errRaisesException=True):
    if isinstance(req,str):
        req = {"req":req}

    if args:
        req = dict(req, **args)

    rsp = card.Transaction(req)
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
    "mode":"continuous",
    "sync":True, 
    "product":opts.product_uid
    }

sendRequest("hub.set", hubConfig)
logging.info(f"HUB INFO  ProductUID: {hubConfig['product']}  Sync: {hubConfig['sync']}")


## Configure Baseline Web Request
webReq = {"req":"web.post",
    "payload":"",
    "seconds":2,
    "route":opts.route,
    "offset":0,
    "total":0
    }

## Generate and Perform Web Request from Chunk of file Bytes
def writeWebReqChunk(payload, offset, total):
    webReq['payload'] = str(binascii.b2a_base64(bytes(payload))[:-1], 'utf-8')
    webReq['offset'] = offset
    webReq['total'] = total
    sendRequest(webReq)



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
            payload = p.read(1024)
            numPayloadBytes = len(payload) 
            keepReading = numPayloadBytes >=1024
            
            
            try:
                writeWebReqChunk(payload, numBytes, totalBytes)
            except:
                break

            
            numBytes += numPayloadBytes
             
    
    logging.info(f"Payload Size: {numBytes/1024} KB.")
            

if (opts.file):
    sendFileBytes(opts.file)
else:
    logging.warning("No file selected to parse and send bytes")
