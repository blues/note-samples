import serial
import notecard
import logging
import configargparse
import time
import notecardDataTransfer
import os

# Define default options
DEFAULT_SERIAL_PORT_ID = "COM4"
DEFAULT_PORT_BAUDRATE = 115200
DEFAULT_DEBUG = True
DEFAULT_LOG_FOLDER = './'
DEFAULT_ROUTE_NAME = "ping"
DEFAULT_WEB_REQUEST_TIMEOUT = 30
DEFAULT_MEASURE_TRANSFER_TIME = True
DEFAULT_CONNECTION_TIMEOUT_SECS = 90


## Function to parse command-line arguments
def parseCommandLineArgs():

    DESCRIPTION = """Example for uploading larger files and data to the cloud
    
    """


    p = configargparse.ArgumentParser(description=DESCRIPTION,
                                      default_config_files=['./config.txt'])

    p.add("-p", "--port", help="Serial port identifier for port connected to Notecard", default=DEFAULT_SERIAL_PORT_ID)
    p.add("-b", "--baudrate", help="Serial port baudrate (bps)", default=DEFAULT_PORT_BAUDRATE, type = int)
    p.add("-r", "--route", help="Name of route Notecard web request transactions will use", default=DEFAULT_ROUTE_NAME)
    p.add("-f", "--file", help="File to use as data source for transfer", required=True)
    p.add("-c", "--connection-timeout", help="Time in seconds to wait for Notecard to connect to Notehub before throwing exception", default=DEFAULT_CONNECTION_TIMEOUT_SECS, type=int)
    p.add("-d", "--debug", help="Log debug messages", action='store_true')
    p.add("-l", "--log-folder", help="Directory where log files are stored", default=DEFAULT_LOG_FOLDER, env_var="LOG_FOLDER")
    p.add("-m", "--mode", help="Notecard connection mode to Notehub (continuous, periodic, minimum)")
    p.add("-u", "--product-uid", help="Notehub Product UID (com.company.name.project)", env_var="PRODUCT_UID")
    p.add("-t", "--timeout", help="Web request timeout in seconds", default=DEFAULT_WEB_REQUEST_TIMEOUT, type=int)
    p.add("-i", "--include-file-name", help="Add file name as query parameter to web request", action='store_true')
    p.add("-e", "--measure-elapsed-time", help="Measure how long the file transfer process takes", action='store_true')
    p.add("--legacy", help="Use legacy method to upload file. Uses base64 encoding in web transaction payloads", action='store_true')
    p.add("-B", "--binary-size", help="Size of binary data to send in each transaction", type=int)

    opts = p.parse_args()
    hub_config = {}
    if opts.mode:
        hub_config['mode'] = opts.mode
        hub_config['sync'] = True

    if opts.product_uid:
        hub_config['product'] = opts.product_uid

    opts.hub_config = None if hub_config=={} else hub_config

    return opts




def connectToNotecard(opts):
    ## Connect to Notecard
    port = serial.Serial(opts.port, baudrate=opts.baudrate)
    card = notecard.OpenSerial(port, debug=opts.debug)

    return card


## Notecard Request Method
def sendRequest(card, req, args=None, errRaisesException=True):
    if isinstance(req,str):
        req = {"req":req}

    if args:
        req = dict(req, **args)

    logging.debug(req)
    rsp = card.Transaction(req)
    logging.debug(rsp)
    if errRaisesException and 'err' in rsp:
        raise Exception("Notecard Transaction Error: " + rsp['err'])

    return rsp


def main():

    ## Get options
    opts = parseCommandLineArgs()


    ## Configure logging
    if opts.debug:
        logFolder = opts.log_folder.rstrip("/\\")
        logLevel = logging.DEBUG
        logging.basicConfig(
            level=logLevel,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(f'{logFolder}/{time.strftime("%Y%m%d-%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )

    logging.info(opts)

    card = connectToNotecard(opts)
        
    ## Log Notecard Info
    rsp = sendRequest(card, "card.version")
    logging.info(f"NOTECARD INFO Device: {rsp['device']} SKU: {rsp['sku']} Firmware Version: {rsp['version']}")


    if opts.hub_config:
        sendRequest(card, "hub.set", opts.hub_config)
        logging.info(f"HUB config: {opts.hub_config}")

    uploader = (notecardDataTransfer.BinaryDataUploaderLegacy(card, opts.route, printFcn=logging.debug, timeout=opts.timeout)
                if opts.legacy
                else notecardDataTransfer.BinaryDataUploader(card, opts.route, printFcn=logging.debug, timeout=opts.timeout))
    
    if opts.include_file_name:
        fileName = os.path.basename(os.path.normpath(opts.file))
        uploader.setFileName(fileName)

    if opts.binary_size:
        uploader.setBinaryBuffSize(opts.binary_size)

    startTime = 0
    fileSizeInBytes = 0
    with open(opts.file, 'rb') as f:
        startTime = time.time()
        uploader.upload(f)
        endTime = time.time()
        fileSizeInBytes = f.seek(0,2)


    if opts.measure_elapsed_time:
        logging.info(f"Sent file: {opts.file}\n{fileSizeInBytes/1024} KB\n{endTime-startTime} seconds")

if __name__ == "__main__":
    main()



