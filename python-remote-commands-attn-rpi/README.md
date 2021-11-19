# Python Raspberry Pi ATTN Pin

Example of how to use the ATTN Pin with Python on a Raspberry Pi

## Description
Send commands or requests from Notehub cloud service to Python application via the Notecard and ATTN Pin

General workflow follows:
1. A Notehub API request is made to enqueue a command to by executed by the Python application
2. Notecard downloads enqueued commands on the next cloud sync with Notehub
3. The Notecard ATTN pin goes HIGH when the command queue is downloaded to Notecard
4. The Python App triggers an interrupt service routine (ISR) to flag ATTN pin is now HIGH
5. The Python App queries the ATTN pin for the source of the trigger (in this case a Notefile update)
6. The Python App queries the Notecard command queue for commands and adds them to a list of tasks to execute
7. The Python App executes all the tasks in the list of tasks




## Setup Hardware
Notecard connected to a Raspberry Pi with Python 3 installed

The Notecard ATTN Pin is wired to a GPIO pin on the Rasberry Pi

The data connection can be I2C, UART (RS232), or USB 

This example default configuration is for use with Notecarrier PI mounted on a Raspberry Pi.

If using a [Notecarrier PI](https://dev.blues.io/hardware/notecarrier-datasheet/notecarrier-pi/), ensure the [ATTN switch](https://dev.blues.io/hardware/notecarrier-datasheet/notecarrier-pi/#dip-switches) is enabled


## Install Application Python Requirements

```bash
pip3 install -r requirements.txt
```


## Configure Application

System environment variables are used to configure the example application

|Name|Default Value|Description|Info|
|----|-------------|-----------|----|
|PRODUCT_UID|com.my.email:uid|Notehub project identifier|REQUIRED.  The default value will not function correctly without configuring this environment variable|
|PORT_TYPE| i2c | Selects communication method with Notecard| Select from {i2c, uart, usb} Uses UART for USB connections|
|PORT_NAME|/dev/i2c-1| Port name used to connect to Notecard| Defaults to I2C for use on Raspberry Pi. Use serial port name when using a UART connection|
|BAUD_RATE|9600| Baud rate in bits-per-second when using UART| Options: {9600,115200}. 115200 is only valid when using auxillary UART|
|DEBUG|false| Display Notecard request and response messages| Options: {true,false}|

   ### Set environment variables
   **Linux**
   ```bash
   $ export PRODUCT_UID=com.my.email:uid
   ```


## Run the Application
```bash
python3 main.py
```



## Send a Command Via Notehub
Commands for the Python application can be enqueue on Notehub using the following

```bash

curl --request POST --url https://api.notefile.net/req --header 'content-type: application/json' --header 'x-session-token: [NOTEHUB_ACCESS_TOKEN]' --data '{"req":"note.add","file":"commands.qi","body":{"print":"hello","count":{"min":1,"inc":2,"max":7}},"device":"[DEVICE_UID]","project":"[PROJECT_UID]"}'

```

The commands are in JSON format and appear in the "body" field of the JSON request above.
The structure is
```json
{ ...
  "body":{
      "command-name-1":["argument1", "argument2"], 
      "command-name-2":"argument1"
    }
  ...
}
```
where the name of the command to be executed `command-name-x`. The arguments of the command are the value of the `command-name-x` field.

Arguments are in a JSON Array. If there is only one argument, then the JSON array is not required, unless the one argument is also a JSON array.

*Valid Commands*
 * `count` - increment a counter from a minimum value to a maximum value at a specific interval.  Has default values `min:0, inc:1, max:10`

 * `print` - display text on the Raspberry Pi terminal where the application is running


### Notehub API Elements
|Name|Description|More Details|
|----|-----------|----|
|[NOTEHUB_ACCESS_TOKEN]|Token string required for Notehub API access| [API Introduction][api intro]|
|[DEVICE_UID]|Notecard unique identifier. In the form `dev:xxxxxxxxxxxxxxx`| [Obtain Device UID](#obtain-device-uid)|
|[PROJECT_UID]|Notehub project unique identifier. `app:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx`| [Obtain Project UID](#obtain-project-uid)| 



### Obtain Device UID
*From Notehub*
1. Navigate to notehub.io
2. Select the Project the Notecard is connecting to
3. Click "Devices" on the left hand side
4. Locate the specific device (if more than one) in the table
5. Double-click the row of the device you want
6. In the Summary pane of the details view, click the "copy" icon next to the "Device UID"

You can also get the list of devices via the [Notehub API](https://dev.blues.io/reference/notehub-api/device-api/#get-devices)

*From Notecard*
1. Plug in a USB cable between the Notecarrier micro USB port and a laptop
2. Using a Chrome-based browser, navigate to dev.blues.io/notecard-playground/
3. Click "Connect" button
4. Select the serial connection for the Notecard 
5. Click "OK"
6. Enter `info` at the terminal prompt
7. Copy the Device UID that is displayed in the response log

### Obtain Project UID
*From Notehub*
1. Navigate to notehub.io
2. Select the Project the Notecard is connecting to
3. Click "Settings" on the left hand side
4. On the right-hand pane scroll down to "Project UID"
5. Click the "copy" icon next to the unique identifier

## Documentation

The documentation for the Notehub API can be found
[here][api intro]).


## Contributing

We love issues, fixes, and pull requests from everyone. By participating in
this project, you agree to abide by the Blues Inc [code of conduct].

For details on contributions we accept and the process for contributing, see
our [contribution guide](CONTRIBUTING.md).

## Running the Tests

If you're planning to contribute to this repo, please be sure to run the tests
before submitting a PR. First run:

```bash
pip3 install -r requirements.txt
```

Then, run the tests using:

```bash
python3 -m pytest
```


## More Information
To learn more about Blues Wireless, the Notecard and Notehub, see:

* [blues.com](https://blues.com)
* [notehub.io][Notehub]
* [wireless.dev](https://wireless.dev)

## License

Copyright (c) 2021 Blues Inc. Released under the MIT license. See
[LICENSE](LICENSE) for details.

[code of conduct]: https://blues.github.io/opensource/code-of-conduct
[Notehub]: https://notehub.io
[api intro]: https://dev.blues.io/reference/notehub-api/api-introduction/