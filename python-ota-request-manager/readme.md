# Firmware Update Script

Update specific Notecards part of a Notehub project to a specific firmware file, and record the update information in the device comments to act as a firmware update log.

## Getting Started

1. Obtain a Notehub API [session token](https://dev.blues.io/api-reference/notehub-api/api-introduction/#authentication-with-session-tokens-deprecated)
2. Obtain the Notehub [Project UID](https://dev.blues.io/api-reference/glossary/#projectuid) (`app:xxxxxx-xxxx-xxxx-xxxx-xxxxxxx`)
3. Determine the firmware type (`card` or `user`)
4. Determine the name of the file to update to (`notecard-x.y.z$20240202111213.bin`)
5. Determine which Notecards to update by the device UID (`dev:xxxxxxxxxxxxxxxx`)
6. Navigate to the folder where the `firmwareUpdate` utility is installed
7. Create a folder to store any generated log files

   ```bash
   >> mkdir .logs
   ```

8. Activate the Python Virtual environment

   ``` bash
   >> .venv/Scripts/activate
   ```

9. Enter the following at the system command prompt

   ```bash
   python main.py -t <user-token> -p <project-uid> -f <firmware-file-name> -w <card or user> -d <device-uid-1> <device-uid-2> <device-uid-3> --dryrun
   ```

   Include the `--dryrun` flag to test the procedure without actually requesting the update to the device.  To enable the update, remove the `--dryrun` flag

10. Wait

The process will print out a JSON formatted report of all of the devices updated.

To see this list of available options, enter

```bash
>> python main.py --help
```

## Selecting Firmware File

When a firmware file is uploaded to Notehub, the file name is amended with a timestamp.

You must use the name of the file created by the upload process, and that includes the timestamp.

### Available Files

To see what files are available in your Notehub Project select **Settings > Firmware** in the Notehub project.

Here you can view both user defined and Notecard firmware files

### Selecting Firmware Type

|`card`|or|`user`|
|---|---|---|

It's important to select the appropriate firmware type to be either `user` or `card`.

The default is `user`, so it will attempt to pass the firmware file to the host MCU connected to the Notecard.

Selecting `card` is required to update the Notecard's own firmware.

## Install Requirements

- Python 3.11
- Pip package manager

### Packages

Check [requirements.txt](requirements.txt)

### Instructions

1. Download the folder containing this readme
2. In the downloaded location, create a Python virtual environment

   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment

   ```bash
   >> .venv/Scripts/activate
   ```

4. Install the required packages

   ```bash
   pip install -r requirements.txt
   ```
