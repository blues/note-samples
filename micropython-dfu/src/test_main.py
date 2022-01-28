

import notecard
import config
import update
import dfu
import version


"""note-python MicroPython example.

This file contains a complete working sample for using the note-python
library on a MicroPython device.
"""
import sys
import time


if sys.implementation.name != 'micropython':
    raise Exception("Please run this example in a MicroPython environment.")

from machine import UART  # noqa: E402
from machine import I2C  # noqa: E402
from machine import Pin


def NotecardExceptionInfo(exception):
    """Construct a formatted Exception string.

    Args:
        exception (Exception): An exception object.

    Returns:
        string: a summary of the exception with line number and details.
    """
    name = exception.__class__.__name__
    return sys.platform + ": " + name + ": " \
        + ' '.join(map(str, exception.args))


def configure_notecard(card, appConfig):
    """Submit a simple JSON-based request to the Notecard.

    Args:
        card (object): An instance of the Notecard class

    """
    req = {"req": "hub.set"}
    req["product"] = appConfig.ProductUID
    req["mode"] = "continuous"
    req["host"] = appConfig.HubHost

    try:
        card.Transaction(req)
    except Exception as exception:
        print("Transaction error: " + NotecardExceptionInfo(exception))
        time.sleep(5)


use_uart = True

def connect_notecard(appConfig):
    """Connect to Notcard and run a transaction test."""
    print("Opening port...")
    try:
        if use_uart:
            port = UART(0, 9600, parity=None, stop=1, bits=8, rx=Pin(17), tx=Pin(16), timeout=1000)
            
        else:
            port = I2C()
    except Exception as exception:
        raise Exception("error opening port: "
                        + NotecardExceptionInfo(exception))

    print("Opening Notecard...")
    try:
        if use_uart:
            card = notecard.OpenSerial(port, debug=True)
        else:
            card = notecard.OpenI2C(port, 0, 0, debug=True)
    except Exception as exception:
        raise Exception("error opening notecard: "
                        + NotecardExceptionInfo(exception))

    return card


def printStatus(message, percentComplete=None):
    if percentComplete is not None:
        print(f"{message}: {percentComplete}% complete")
        return

    print(message)

    


def isExpiredMS(timer):
    return time.ticks_ms() > timer

def setTimerMS(periodMS):
    return time.ticks_ms() + periodMS



def main():

    appConfig = config.loadConfig("secrets.json")

    
    card = connect_notecard(appConfig)
    
    dfu.setVersion(card, version.versionStr)
    
    configure_notecard(card, appConfig)

    updateManager = update.UpdateManager(card, printStatus)

    updateAvailable = False
    updateTimer = 0

    while True:

        if updateAvailable:
            printStatus("Update is available")
            updateManager.migrateAndInstall(restart=False)

        if isExpiredMS(updateTimer):
            printStatus("Checking for update")
            updateTimer = setTimerMS(10000)
            updateAvailable = dfu.isUpdateAvailable(card)


        




main()