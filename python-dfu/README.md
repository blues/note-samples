# Python Notecard DFU

This sample shows how to use the Notecard to update a Python application.  

## Supported Platforms

- Raspberry Pi Pico running Micropython
- [TODO] SWAN runing circuitpython
- Raspberry Pi running Linux OS with CPython v3
- Laptop or PC with standard OS and CPython v3

## Hardware Setup

### Raspberry Pi Pico

| | |
|---|---|
|Notecard Interface Options| {UART, I2C}|
|Default Notecard Interface| UART0 (GPIO pins 16 and 17)|
|MCU Platform| Micropython|
|MCU Python version| Micropython |
|MCU Debug Interface| USB|

*Example Configuration*

   ```json
   // secrets.json
   {
      "product_uid":"my-secret-product-uid",
      "debug": false
   }
   ```

### Raspberry Pi 4

| | |
|---|---|
|Notecard Interface Options| {UART, I2C, USB}|
|Default Notecard Interface| I2C ([Notecarrier PI][notecarrier-pi-kit])*|
|MCU Platform| Linux|
|MCU Python version| Python3 |
|MCU Debug Interface| SSH terminal|

*Default configuration is for use with [Notecarrier PI][notecarrier-pi-kit] mounted on a Raspberry Pi 4

*Example Configuration*

```json
   // secrets.json
   {
      "product_uid":"my-secret-product-uid",
      "debug": false,
      "port_type": "i2c",
      "port_id": "/dev/i2c-1"
   }
   ```

### PC with Standard OS

| | |
|---|---|
|Notecard Interface Options| {USB, UART, I2C}|
|Default Notecard Interface| USB*|
|MCU Platform| Linux/Windows|
|MCU Python version| Python3 |
|MCU Debug Interface| system terminal|

Notecard USB appears as serial port on PC.  You can select USB or UART and get the same results.

*Example Configuration*

```json
   // secrets.json
   {
      "product_uid":"my-secret-product-uid",
      "debug": false,
      "port_type": "usb",
      "port_id": "COM4"
   }
```

## Application Overview
The main application establishes a periodic loop that will execute the next step in the firmware update process. The steps are small, and should not block execution for very long.

TODO - include example of a blocking version of the firmware update process, not just the version that can be used in a background process

## Application Configuration

A `secrets.json` file is used to store application configuration information

Create this file in the same location as `main.py`.  

For the Raspberry Pi Pico, you will need to create and copy this file onto the Raspberry Pi Pico

The format of the file is JSON, where the root field names are the configuration parameters, with the values assigned as the associated configuration values

### Configuration Parameters

|Name|Default Value|Description|Info|
|----|-------------|-----------|----|
|product_uid|*(empty)*|Notehub project identifier|**REQUIRED**  The application will not function correctly without setting this parameter to a valid product UID|
|port_type| uart | Selects communication method with Notecard| Select from {`i2c`, `uart`, `usb`} (USB is also a UART connection)|
|port_id|0| Port identifier used to connect to Notecard| Defaults is UART0 on Raspberry Pi Pico. Use serial port name in a string (for example) `"COM4"` using a UART connection on a standard OS.  Use the I2C numeric port ID for I2C|
|port_baudrate|9600| Baud rate in bits-per-second when using UART| Options are {9600,115200}. 115200 is only valid when using auxillary UART|
|debug|true| Display Notecard request and response messages| Options: {true,false}|

### Configuration Formatting

```json
   // secrets.json
   {
      "product_uid":"my-secret-product-uid",
      "port_type": "uart",
      "port_id": "COM4",
      "port_baudrate": 9600,
      "debug": true
   }
```

## Application Installation and Execution

### Raspberry Pi Pico with Micropython

1. Create a `secrets.json` file in the root folder
2. Execute `deploy-micropy.cmd` **OR**
   Copy the following to the Raspberry Pi Pico
   |Source|Destination|
   |---|---|
   |`secrets.json`|`./secrets.json`|
   |`app`|`./`|
   |`lib`|`./lib`|
   |`src`|`./`|

3. Restart the Pico
4.  Open a serial terminal to monitor output from Pico over USB connection
5.  Restart the Pico to begin execution

### Raspberry Pi or PC with Python 3

1. Clone this repository
2. Create `secrets.json` file in the root folder
3. Run `pip install -r requirements.txt` to install all of the prerequisites.
4. Run `chmod a+x app/main.py` to allow `app/main.py` to reload itself after it loads an updated file.
5. Run `python3 app/main.py`

## Perform Update

   1. Modify `app/version.py` to a new version number

   2. Generate a TAR-file that includes `app/version.py`

      A utility script `generateTarFile.sh` can be used to create new TAR-file from the contents of the `app` folder

   3. Upload the TAR-file to your Notehub project using the steps outlined here: <https://dev.blues.io/notehub/notehub-walkthrough/#manage-host-firmware>

   4. Deploy the TAR-file to your Notecard by following: <https://dev.blues.io/notehub/notehub-walkthrough/#deploy-firmware>
   5. After the installation completes, Notehub should register a new version that matches the change in *step 1*



## Development and Testing
For doing additional development work and executing tests refer to the following sections

### Installing Development and Testing Python Packages

To install all of the package prerequisites
```
pip install -r requirements-ci.txt
``` 

Use the `runtests.py` script to execute test suite with code coverage.
```
python runtests.py
```

### Install `ampy` to Deploy to Micropython
The Micropython update scripts use [`ampy`](https://pypi.org/project/adafruit-ampy/) to copy source files to the microprocessor.

To install `ampy`
```
pip install adafruit-ampy
```

> ❗ **Configure Serial Port**: Be sure to set the correct serial port by setting the `AMPY_PORT` environment variable.

_Linux/Mac_
```
export AMPY_PORT=/dev/tty.SLAB_USBtoUART
```

_Windows_
```
set AMPY_PORT=COM4
```

### Update Notecard SDK for Micropython
For convenience in copying the SDK package to the microprocessor, this repository contains a copy of the Notecard SDK `note-python`

To update the version of the Notecard SDK you can copy the contents of the latest `note-python` version to `./lib/notecard`

1. Download the latest release here: https://github.com/blues/note-python/releases
2. Extract the ZIP-archive
3. Copy the contents of the `notecard` directory to `./lib/notecard`
4. Execute `ampy` to copy `lib` folder to the microprocessor
   ```
   ampy put lib lib
   ```
   

### Repository Layout
#### **src**
Python source for modules that define OTA update process
|| |
|---|---|
|`dfu`| abstracts the interactions with Notecard to migrate the content from the Notecard to the host processor|
|`updater`| state machine for managing file update process. See [doc\dfuFlow.md](doc\dfuFlow.md) for more details|
|`utarfile`| reading and extracting content from TAR-file|

#### **test**
Unit tests for modules in `src`

#### **app**
Python files defining example main host MCU application.  Application written to work in Python3 and Micropython executing on Raspberry Pi Pico.
|| |
|---|---|
|`config`| class defining application configuration and defaults|
|`version`| class defining current application version info|
|`main`| entry point file. Establishes configuration, connects to Notecard, and executes main loop|


#### **lib**
Source for Python modules to augment Micropython
|||
|---|---|
|`haslibextras`| implement MD5 hash function, which is not available in `hashlib` library in Micropython|
|`notecard`| Notecard SDK|
|`abc`| stub implementation for Python abstract classes which are not supported in Micropython|


[notecarrier-pi-kit]:https://shop.blues.io/products/raspberry-pi-starter-kit
