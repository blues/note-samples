

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



    
if sys.implementation.name == 'micropython':
    from machine import UART, reset_cause  # noqa: E402
    from machine import I2C  # noqa: E402
    from machine import Pin
    from machine import reset

    def getTimeMS():
        return time.ticks_ms()
    
    def connect_notecard(appConfig):
        """Connect to Notcard and run a transaction test."""
        print("Opening port...")
        use_uart = appConfig.PortType == config.PortType.UART or appConfig.PortType == config.PortType.USB
        try:
            if use_uart:
                uartMethodTimeoutMS = 10000
                port = UART(appConfig.PortID, appConfig.PortBaudRate, parity=None, stop=1, bits=8, rx=Pin(17), tx=Pin(16), timeout=uartMethodTimeoutMS)
                
            else:
                port = I2C()
        except Exception as exception:
            raise Exception("error opening port: "
                            + NotecardExceptionInfo(exception))

        print("Opening Notecard...")
        try:
            if use_uart:
                card = notecard.OpenSerial(port, debug=appConfig.Debug)
            else:
                card = notecard.OpenI2C(port, 0, 0, debug=appConfig.Debug)
        except Exception as exception:
            raise Exception("error opening notecard: "
                            + NotecardExceptionInfo(exception))

        return card


elif sys.implementation.name == 'cpython':

    def getTimeMS():
        return time.time_ns() // 1E6


    import serial
    import os
    
    def connect_notecard(appConfig):
        """Connect to Notcard and run a transaction test."""
        print("Opening port...")
        use_uart = appConfig.PortType == config.PortType.UART or appConfig.PortType == config.PortType.USB

        if not use_uart:
            raise Exception("only supports UART in CPython implementations")

        try:
            port = serial.Serial(port=appConfig.PortID,
                                 baudrate=appConfig.PortBaudRate)
        except Exception as exception:
            raise Exception("error opening port: "
                            + NotecardExceptionInfo(exception))

        print("Opening Notecard...")
        try:
            card = notecard.OpenSerial(port, debug=appConfig.Debug)
        except Exception as exception:
            raise Exception("error opening notecard: "
                            + NotecardExceptionInfo(exception))

        return card

    def reset():
        mainName = __file__
        print(f"Restarting program{mainName}")
        os.execv(sys.executable, [f'python {mainName}'] + sys.argv[1:])

else:
    raise Exception("Please run this example in a MicroPython or CPython environment.")


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
    req["sync"] = True
    req["inbound"] = 1

    try:
        card.Transaction(req)
    except Exception as exception:
        print("Transaction error: " + NotecardExceptionInfo(exception))
        time.sleep(5)


def printStatus(message, percentComplete=None):
    if percentComplete is not None:
        print(f"{message}: {percentComplete}% complete")
        return

    print(message)

    


def isExpiredMS(timer):
    return getTimeMS() > timer

def setTimerMS(periodMS):
    return getTimeMS() + periodMS

def main():

    appConfig = config.loadConfig("secrets.json")

    
    card = connect_notecard(appConfig)
    
    print(f"Version: {version.versionStr}")

    dfu.setVersion(card, version.versionStr)
    
    configure_notecard(card, appConfig)

    updateManager = update.UpdateManager(card, printStatus)
    updateManager.restart = reset

    updateAvailable = False
    updateTimer = 0

    while True:

        if updateAvailable:
            printStatus("Update is available")
            try:
                updateManager.migrateAndInstall(restart=True)
            finally:
                updateAvailable = False
            

        if isExpiredMS(updateTimer):
            printStatus(f"Current Version: {version.versionStr}")
            printStatus("Checking for update")
            updateTimer = setTimerMS(10000)
            updateAvailable = dfu.isUpdateAvailable(card)


        




main()