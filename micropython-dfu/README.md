# Micropython File Downloader Sample for Pico

This sample shows how to use the Notecard to update the application on a Raspberry Pi Pico that is running Micropython. 

This sample can also be used on standard OS machines running CPython


## Hardware Setup

### Raspberry Pi Pico

Notecard connected to a Raspberry Pi Pico via UART0 (GPIO pins 16 and 17)

The Raspberry Pi Pico us configured to use Micropython

This example can be configured to use I2C (see below)


### Python 3 on Standard OS

Notecard connected to a PC, Laptop, or Linux-based single board computer with Python 3 installed

This could be via a USB connection, UART, or I2C.

This example default configuration is for use with Notecarrier-PI mounted on a Raspberry Pi.


## Application Installation


### Raspberry Pi Pico

1. Copy the entire contents of the `src` folder to the Raspberry Pi Pico (including the `src/lib` folder)
2. Restart the Pico
3. Open a serial terminal to monitor output from Pico over USB connection
   
### Python 3 on Standard OS

1. Add a directory to your Pi and copy the contents of `src` (but _not_ `src/lib`) into that directory.
2. Change the current directory to the application directory 
3. Run `pip install -r requirements.txt` to install all of the prerequisites.
4. Run `chmod a+x main.py` to allow `main.py` to reload itself after it loads an updated file.


## Application Configuration

A `secrets.json` file is used to store application configuration information

Create this file in the same location as `main.py`.  For the Raspberry Pi Pico, you will need to create and copy this file onto the Raspberry Pi Pico

The format of the file is JSON, where the root field names are the configuration parameters, with the values assigned as the associated configuration values

### Configuration Parameters

|Name|Default Value|Description|Info|
|----|-------------|-----------|----|
|product_uid|_(empty)_|Notehub project identifier|**REQUIRED**  The application will not function correctly without setting this parameter to a valid product UID|
|port_type| uart | Selects communication method with Notecard| Select from {`i2c`, `uart`, `usb`} (USB is also a UART connection)|
|port_id|0| Port identifier used to connect to Notecard| Defaults is UART0 on Raspberry Pi Pico. Use serial port name in a string (for example) `"COM4"` using a UART connection on a standard OS.  Use the I2C numeric port ID for I2C|
|port_baudrate|9600| Baud rate in bits-per-second when using UART| Options are {9600,115200}. 115200 is only valid when using auxillary UART|
|debug|true| Display Notecard request and response messages| Options: {true,false}|

   ### Example Configuration Files
   **Raspberry Pi Pico**
   ```json
   // secrets.json
   {
      "product_uid":"my-secret-product-uid",
      "debug": false
   }
   ```

   **Windows**
   
   Using UART or USB connection
   ```json
   // secrets.json
   {
      "product_uid":"my-secret-product-uid",
      "debug": false,
      "port_type": "uart",
      "port_id": "COM4"
   }
   
   ```
   **Linux**
   
   Using I2C connection
   ```json
   // secrets.json
   {
      "product_uid":"my-secret-product-uid",
      "debug": false,
      "port_type": "i2c",
      "port_id": "/dev/i2c-1"
   }
   ```


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



## Sample Application Flow

1. A `TAR-file` file is uploaded to Notehub.
2. A specific Notecard instance is updated with information about the file transfer
3. Notecard detects the file transfer request on the next sync with Notehub
4. Notecard starts the file transfer process.  
5. Notecard stores the file on it's own file system until it has been completely downloaded. (Depending on the size of the file, this may take several connection cycles)
6. Notecard updates the flag indicating a file is ready for migration to the host.

At this point the example Python application will manage the migration process.

7. The host application detects the file is ready for migration 
8. The host application requests Notecard enter DFU mode, and waits until DFU mode is enabled.
9. The host application requests the file bytes, and checks the bytes transferred correctly using checksums.
10. Once the entire file is transferred and validated, the host application extracts the contents of the TAR-file
11. After extraction, the host MCU restarts
12. Upon restarting, the host application sets the host application firmware version
13. On it's next sync, Notecard will push this version information to Notehub, where it will now be displayed as the current version information for the host application on Notehub for that specific Notecard.

**A couple of things:**
* Notecard disables syncing to the cloud when in DFU mode.  
* Upon exiting DFU mode, Notecard will attempt to reconnect to the cloud using the previous "hub" settings
  
