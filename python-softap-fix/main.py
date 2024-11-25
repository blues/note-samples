"""Notecard SoftAP fix.

Script to fix missing SoftAP assets on Notecard.
This script will download a zip file from a remote server and write them to the WiFi area of the Notecard.
"""
import sys
import hashlib
import time
from pathlib import Path
from requests import get
import base64
import serial
from notecard import OpenSerial, Notecard
from argparse import ArgumentParser
from serial.tools import list_ports

if sys.implementation.name != 'cpython':
    raise Exception("Please run this example in a CPython environment.")


AFFECTED_SKU = ["NOTE-ESP"]

# URL to download the SoftAP assets from
REMOTE_ASSETS_URL = "https://s3.us-east-1.amazonaws.com/note-esp-softap"
REMOTE_ASSETS_MANIFEST_MAP = {
    "eyehide.png": "eyehide.png",
    "eyeshow.png": "eyeshow.png",
    "favicon.png": "favicon.png",
    "index.shtml": "index.sht",
    "jquery_2.2.4.min.js": "jquery22.js",
    "logo.png": "logo.png",
    "style.css": "style.css"
}

def NotecardExceptionInfo(exception: Exception) -> str:
    """Construct a formatted Exception string.

    Args:
        exception (Exception): An exception object.

    Returns:
        string: a summary of the exception with line number and details.
    """
    s1 = '{}'.format(sys.exc_info()[-1].tb_lineno)
    s2 = exception.__class__.__name__
    return "line " + s1 + ": " + s2 + ": " + ' '.join(map(str, exception.args))


def write_note(card: Notecard, file_path: Path) -> None:
    """Write a file to the wifi area of the Notecard.

    Args:
        card (Notecard): An instance of the Notecard class
        file_path (str): The path to the file to write
    """
    # Set request to 'fast' mode
    card.CARD_REQUEST_SEGMENT_MAX_LEN = 8192
    card.CARD_REQUEST_SEGMENT_DELAY_MS = 0

    with open(file_path, "rb") as f:
        contents = f.read()

    # Send it to the card in chunks (https://github.com/blues/notecard/blob/b05368a7c5afb0bb6e1bf338664855d8bcf57ad6/tools/testcard/write.go#L20)
    chunk_size = 4096 
    total_length = len(contents)
    length_left = total_length
    chunk_offset = 0

    while length_left > 0:
        # Construct the chunk
        chunk_length = min(length_left, chunk_size)
        chunk = contents[chunk_offset:chunk_offset + chunk_length]
        chunk_md5 = hashlib.md5(chunk).hexdigest()

        chunk_base64 = base64.b64encode(chunk).decode('utf-8')

        req = {
            "req": "card.file",
            "mode": "write-range",
            "area": "wifi",
            "name": file_path.name,
            "status": chunk_md5,
            "version": hashlib.md5(chunk_md5.encode()).hexdigest(),
            "offset": chunk_offset,
            "length": chunk_length,
            "payload": chunk_base64
        }

        try:
            card.Transaction(req)
        except Exception as exception:
            print("Transaction error: " + NotecardExceptionInfo(exception))
            time.sleep(5)

        # Increment the chunk index
        chunk_offset += chunk_length
        length_left -= chunk_length


def download_and_extract(url: str) -> Path:
    """Download a file.

    Args:
        url (str): URL to download from

    Returns:
        Path: Path to downloaded file
    """
    try:
        response = get(url)
        response.raise_for_status()
        file_path = Path.cwd() / "assets" / REMOTE_ASSETS_MANIFEST_MAP[Path(url).name]

        with open(file_path, 'wb') as file:
            file.write(response.content)

        return file_path
    except Exception as e:
        raise Exception(f"Download failed: {e}")


def download_assets() -> None:
    Path.cwd().joinpath("assets").mkdir(parents=True, exist_ok=True)
    for asset in REMOTE_ASSETS_MANIFEST_MAP.keys():
        download_and_extract(f"{REMOTE_ASSETS_URL}/{asset}")


def is_affected_notecard_sku(card: Notecard) -> bool:
    req = {"req":"card.version"}

    try:
        res = card.Transaction(req)
    except Exception as exception:
        raise Exception(f"error checking Notecard SKU: {NotecardExceptionInfo(exception)}")

    sku = res.get("sku")
    if sku is None:
        return False
    
    return sku in AFFECTED_SKU


def update_card_files(card: Notecard) -> None:
    files = list(Path.cwd().joinpath("assets").iterdir())
    total_files = len(files)

    for index, file_path in enumerate(files, 1):
        print(f"{file_path.name} ({index} of {total_files})...")
        write_note(card, file_path)


def process_card_on_port(portId: str) -> None:
    print(f"Opening port {portId}...")
    with serial.Serial(port=portId) as port:
        print("Opening Notecard...")
        try:
            card = OpenSerial(port)
        except Exception as exception:
            raise Exception(f"error opening notecard: {NotecardExceptionInfo(exception)}")
        
        print("Checking Notecard SKU...")
        if not is_affected_notecard_sku(card):
            print(f"Notecard on port {portId} is not an affected SKU")
            return

        print("Writing files to Notecard, please wait...")
        update_card_files(card)
        print("Complete.")


def getPortFromCommandLineArguments() -> None:
    prog = "Wifi SoftAP Fix"
    description = """Notecard WiFi SoftAP fix.
                Script to fix missing SoftAP assets on Notecard.
                This script will download a zip file from a remote server and write them to the WiFi area of the Notecard.
                """
    parser = ArgumentParser(prog=prog, description=description)
    parser.add_argument('-p', '--port', required=False, help="UART Serial port identifier.  Windows - COMXX, Linux - /dev/serial0, Mac - /dev/tty.usbmodemNOTE1")

    opts = parser.parse_args()

    return opts.port


def getNotecardSerialPorts() -> None:
    defaultPortLookup = {"linux": "/dev/serial0",
                        "linux2": "/dev/serial0",
                        "darwin": "/dev/tty.usbmodemNOTE1",
                        "win32": "COM4"}
    
    portIds = getPortFromCommandLineArguments()

    if portIds is not None:
        return portIds if isinstance(portIds, list) else [portIds]

    print("Detecting serial port...")

    iterator = sorted(list_ports.grep("30A4:"))
    portIds = [p for (p,_,_) in iterator]
        
    if portIds != []:
        return portIds

    print("Serial port not detected. Using default ")
    portIds = defaultPortLookup[sys.platform]
    
    if not isinstance(portIds, list):
        portIds = [portIds]

    return portIds


def main() -> None:
    """Connect to Notecard over Serial and write SoftAP assets to the Notecard."""
    print("Downloading assets...")
    download_assets()
    
    portIds = getNotecardSerialPorts()

    for p in portIds:
        process_card_on_port(p)


if __name__ == "__main__":
    main()
