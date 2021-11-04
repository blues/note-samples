# Python Airnote Data Migration

Transfer data collected on Airnote cloud service (Notehub) and store it in a local data base.

## Description
The general data migration process looks like this:

1. Query list of Airnotes to gather data from

2. Determine the last event data that was stored in the local database for a given Airnote ID

3. Query Notehub (Airnote cloud service) for events that have occurred since that last event stored in the local database (defaults to max of 50 events returned at a time)

4. Filter the query results to data only related to Air Quality Measurements (_air.qo)

5. Store each measurement event to local database, indexed off the event id

6. Repeat steps 3 - 5 until no more data is available on the cloud service for that specific device

7. Repeat steps 2 - 6 for each Airnote returned by step 1


## Usage

### Install Python Requirements

```bash
pip install -r requirements.txt
```

### Add Airnote Device UID
The QR code on the Airnote has a device identifier of the form `dev:xxxxxxxxxxxxxxx`

Add this to the list of devices to query new data from.

From the system command promp, you can use
```bash

python main.py -a dev:xxxxxxxxxxxxxxx

```

### Get Airnote PIN
The PIN acts as a session token, and permits the access to the Notehub API. This example application checks the `NOTEHUB_PIN` environment variable, so the value is not hardcoded into the Python Application

To get the PIN:
1. Scan the QR code on your Airnote
2. View the URL
3. Extract the value `XXXXXX` from url pin query parameter`&pin=XXXXXX`

Store the Airnote in your Python application system environment:

**Linux**
```bash
NOTEHUB_PIN=XXXXXX
```

**Windows**
```shell
set NOTEHUB_PIN=XXXXXX
```

### Migrate Airnote Data
This will download Airnote data for the Airnotes identified by the device ID that were added via the *Add Airnote Device UID* step above.

```bash
python main.py
```

### Export Data to CSV
Output the raw downloaded data to comma-separated value (CSV) file.

```bash
python main.py -x myFile.csv
```

To filter to a specific device
```bash
python main.py -x myFile.csv -d dev:xxxxxxxxxxxxxx
```

### Help on this application
You can view the help for this app by entering the following at the system command prompt
```bash
python main.py -h
```

## Documentation

The documentation for the Notehub API can be found
[here](https://dev.blues.io/reference/notehub-api/api-introduction/).


## Contributing

We love issues, fixes, and pull requests from everyone. By participating in
this project, you agree to abide by the Blues Inc [code of conduct].

For details on contributions we accept and the process for contributing, see
our [contribution guide](CONTRIBUTING.md).

## Running the Tests

If you're planning to contribute to this repo, please be sure to run the tests
before submitting a PR. First run:

```bash
pip install -r requirements.txt
```

Then, run the tests using:

```bash
python -m pytest
```


## More Information

## To learn more about Blues Wireless, the Notecard and Notehub, see:

* [blues.com](https://blues.com)
* [notehub.io][Notehub]
* [wireless.dev](https://wireless.dev)

## License

Copyright (c) 2019 Blues Inc. Released under the MIT license. See
[LICENSE](LICENSE) for details.

[code of conduct]: https://blues.github.io/opensource/code-of-conduct
[Notehub]: https://notehub.io