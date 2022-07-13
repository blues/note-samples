# Python File Downloader

This sample shows how to use the Notecard to update a Python application.  

### Supported Platforms

 - Raspberry Pi Pico running Micropython
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



## Application Selection

|Main|Description|
|---|---|
|main_blocking.py | Executes entire Python firmware update at once|
|main_background.py | Executes Python firmware update one step at a time|

**main_blocking.py**
In the main execution loop, if the application detects that a firmware update is available, then it will begin the update process, but will block all other firmware tasks.

This is a faster and arguably simplier way to do the update, but doesn't permit continued application functionality

**main_background.py**
In the main execution loop, the application invokes the next step in the firmware update process.  The steps are small, and should not block execution for very long.

Depending on how the timing and priority for this method is implemented, it may take longer for it to execute the entire firmware update than the "blocking" version. But it enables the application to perform it's nominal functionality while firmware updates occur when time and cycles are available.


## Application Configuration

A `secrets.json` file is used to store application configuration information

Create this file in the same location as `main_*.py`.  

For the Raspberry Pi Pico, you will need to create and copy this file onto the Raspberry Pi Pico

The format of the file is JSON, where the root field names are the configuration parameters, with the values assigned as the associated configuration values

### Configuration Parameters

|Name|Default Value|Description|Info|
|----|-------------|-----------|----|
|product_uid|_(empty)_|Notehub project identifier|**REQUIRED**  The application will not function correctly without setting this parameter to a valid product UID|
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

1. Create a `secrets.json` file in the `src` folder
2. Copy the entire contents of the `src` folder to the Raspberry Pi Pico (including the `src/lib` folder)
3. Restart the Pico
4. Open a serial terminal to monitor output from Pico over USB connection
5. Restart the Pico to begin execution


### Raspberry Pi or PC with Python 3

   
1. Add a directory to your computer and copy the contents of `src` (but _not_ `src/lib`) into that directory.
2. Create `secrets.json` file in the newly created directory
3. Change the current directory to the application directory 
4. Run `pip install -r requirements.txt` to install all of the prerequisites.
5. Run `chmod a+x main_*.py` to allow `main_*.py` to reload itself after it loads an updated file.



## Running the Application

### Raspberry Pi Pico
1. Restart the Pico


### Python 3 on Standard OS

1. Run `python3 main.py`



## Perform Update
   1. Modify `version.py` to a new version number
   
   2. Generate a TAR-file that includes `version.py`

      A utility script `generateTarFile.sh` can be used to create new TAR-file from the contents of the `src` folder
   
   3. Upload the TAR-file to your Notehub project using the steps outlined here: https://dev.blues.io/notehub/notehub-walkthrough/#manage-host-firmware
   
   4. Deploy the TAR-file to your Notecard by following: https://dev.blues.io/notehub/notehub-walkthrough/#deploy-firmware
   5. After the installation completes, Notehub should register a new version that matches the change in _step 1_



[notecarrier-pi-kit]:https://shop.blues.io/products/raspberry-pi-starter-kit