

gpioAttnPin = 6 # info: https://dev.blues.io/hardware/notecarrier-datasheet/notecarrier-pi/#dip-switches


import notecard
import logging
try:
    import RPi.GPIO as GPIO
except:
    pass
import sys
import signal

import task
from command import Commands as CM
import config
import attn

try:
    from periphery import I2C
except:
    pass

import serial





log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

def connectNotecard(config):
    if config.PortType == 'i2c':
        port = I2C(config.PortName)
        card = notecard.OpenI2C(port, 0, 0, debug=config.EnableDebug)
    else:
        port = serial.Serial(port=config.PortName,baudrate=config.BaudRate)
        card = notecard.OpenSerial(port, debug=config.EnableDebug)

    return card


def configureNotecard(card, productUID, host):

    dataUplinkPeriodMinutes = 1
    dataDownlinkPeriodMinutes = 2

    req = {"req": "hub.set",
            "product":productUID,
            "host":host,
            "mode":"continuous",
            "outbound":dataUplinkPeriodMinutes,
            "inbound":dataDownlinkPeriodMinutes,
            "sync":True,
            "align":True
    }

    card.Transaction(req)


commandTasks = task.TaskQueue()
CM.SetSubmitTaskFn(commandTasks.Add)


AttnFired = False

def startMainLoop():
    global AttnFired
    #Infinite loop that processes tasks
    while True:
        if AttnFired:
            info = attn.QueryTriggerSource(card)
            attn.ProcessAttnInfo(card, info)
            attn.Arm(card)
            AttnFired = False

        commandTasks.ExecuteAll()


GPIO.setmode(GPIO.BCM)

# Configure RPi GPIO pin that is wired to the Notecard ATTN pin to detect rising edges
GPIO.setup(gpioAttnPin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)



def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

if __name__ == '__main__':


    config = config.GetConfig()

    if config.EnableDebug:
        log.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)


    log.info(f"Running: {__file__}")

    message = f"\nProduct: {config.ProductUID}\nHost: {config.HubHost}\nDebug: {config.EnableDebug}\nConnection Port Type:{config.PortType}\nPort name: {config.PortName}\n"
    log.info(message)

    log.debug(f"Connecting to Notecard using {config.PortType} port type")
    card = connectNotecard(config)

    log.debug("Configuring Notecard Hub connection")
    configureNotecard(card, productUID=config.ProductUID, host=config.HubHost)

    attn.ReadCommands(card)

    def attnIsrHandler(channel):
        global AttnFired
        AttnFired = True
       
    GPIO.add_event_detect(gpioAttnPin, GPIO.RISING, callback=attnIsrHandler)

    attn.Initialize(card)

    # Enables killing this script via Ctrl-C
    signal.signal(signal.SIGINT, signal_handler)


    startMainLoop()




