# SoftAP Fix

This script is used to fix Notecard (NOTE-ESP) devices that are missing the
assets required to run SoftAP. This Script should only be run against
ESP32-based Wi-Fi Notecards and not Cell+WiFi or legacy Notecards.

## Requirements

- Python 3

## Usage

1. Make sure you are running Notecard Firmware (`7.4.2` or later). Visit
[blues.dev](https://dev.blues.io/notecard/notecard-firmware-updates/) for
upgrade instructions.

2. Connect the Notecard to your machine via USB (Serial).

3. From a command line, change to the directory containing this `README.md`.

4. Run the instructions below:

   1. **LINUX ONLY:** Create a python virtual environment

    ```bash
    sudo apt install python3 python3-venv
    python3 -m venv blues-env
    source blues-env/bin/activate
    ```

   2. Install requirements and execute the script

    ```bash
    pip install -r requirements.txt
    python main.py
    ```

    > _**NOTE:** By DEFAULT this script attempts to identify which serial port
    > the Notecard is connected.  If it cannot detect which serial port to use,
    > you may need to specify which serial port. If the script is unable to
    > detect the correct port, then you may
    > [manually specify the correct port](#specify-serial-port)_

   3. **LINUX ONLY:** Exit the virtual environment

    ```bash
    deactivate
    ```


### Specify Serial Port (OPTIONAL)

To specify which serial port to use for communicating with the Notecard, use
the following syntax:

```bash
python main.py -p <port-id>
```

where `<port-id>` is the name of the serial port on your operating system.
