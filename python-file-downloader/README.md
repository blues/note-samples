# Python File Downloader Sample

This sample shows how to use the Notecard to update a host single-board computer
(like the Raspberry Pi) with source files from a remote location. 

**Note: This sample applies to linux-based SBCs only. CircuitPython & MicroPython MCUs cannot use this approach.**


## Hardware Setup
Notecard connected to a PC, Laptop, or Linux-based single board computer with Python 3 installed

This could be via a USB connection, UART, or I2C.

This example default configuration is for use with Notecarrier-PI mounted on a Raspberry Pi.


## Application Installation

1. Add a directory to your Pi and copy the contents of [the application folder](application/) into that directory.
2. Change the current directory to the application directory 
3. Run `pip install -r requirements.txt` to install all of the prerequisites.
4. Run `chmod a+x main.py` to allow `main.py` to reload itself after it loads an updated file.


## Application Configuration

System environment variables are used to configure the example application

|Name|Default Value|Description|Info|
|----|-------------|-----------|----|
|PRODUCT_UID|com.my.email:uid|Notehub project identifier|REQUIRED.  The default value will not function correctly without configuring this environment variable|
|PORT_TYPE| i2c | Selects communication method with Notecard| Select from {i2c, uart} Use uart for USB connections|
|PORT|/dev/i2c-1| Port name used to connect to Notecard| Defaults to I2C for use on Raspberry Pi. Use serial port name when using a UART connection|
|BAUD|9600| Baud rate in bits-per-second when using UART| Options are {9600,115200}. 115200 is only valid when using auxillary UART|
|DEBUG|false| Display Notecard request and response messages| Options: {true,false}|

   ### Set environment variables
   **Linux**
   ```bash
   $ export PRODUCT_UID=com.my.email:uid
   ```

   **Windows**
   ```
   > set PRODUCT_UID=com.my.email:uid
   > set PORT_TYPE=uart
   > set PORT=COM4
   ```

## Running the Application

1. Run `python3 src/main.py`


## Perform Update
   1. Create a copy of `main.py`
   
   2. In the copy, modify the value of the `appVersion` variable
   
   for example:
   ```python
     appVersion = "1.7.1"
   ```
   1. Save the file
   
   2. Upload the modified file to your Notehub project using the steps outlined here: https://dev.blues.io/notehub/notehub-walkthrough/#manage-host-firmware
   
   3. Deploy the firmware to your Notecard by following: https://dev.blues.io/notehub/notehub-walkthrough/#deploy-firmware



## Sample Application Flow

1. A `.py` file is uploaded to Notehub.
2. A specific Notecard instance is updated with information about the file transfer
3. Notecard detects the file transfer request on the next sync with Notehub
4. Notecard starts the file transfer process.  
5. Notecard stores the file on it's own file system until it has been completely downloaded. (Depending on the size of the file, this may take several connection cycles)
6. Notecard updates the flag indicating a file is ready for migration to the host.

At this point the example Python application will manage the migration process.

7. The host application detects the file is ready for migration 
8. The host application requests Notecard enter DFU mode, and waits until DFU mode is enabled.
9. The host application requests the file bytes, and checks the bytes transferred correctly using checksums.
10. Once the entire file is transferred and validated, the host application restarts using the new transferred file.
11. Upon restarting, the host application sets the host application firmware version
12. On it's next sync, Notecard will push this version information to Notehub, where it will now be displayed as the current version information for the host application on Notehub for that specific Notecard.

**A couple of things:**
* Notecard disables syncing to the cloud when in DFU mode.  
* Upon exiting DFU mode, Notecard will attempt to reconnect to the cloud using the previous "hub" settings
  
