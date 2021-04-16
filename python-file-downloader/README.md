# Python File Downloader Sample

This sample shows how to use the Notecard to update a host single-board computer
(like the Raspberry Pi) with source files from a remote location. The following
is required to run this sample:

- An Amazon S3 Bucket for source files, [configured to trigger a Lambda function](https://docs.aws.amazon.com/lambda/latest/dg/with-s3-example.html) when files are uploaded. The source for this function is in the [functions/python-file-notifier](functions/python-file-notifier/handler.py) folder.
- A Lambda function, triggered by S3 to notify the Notecard of a new source file. The source for this function is in the [functions/python-file-server](functions/python-file-server/handler.py) folder.
- A Lambda function, called by the Notecard, that serves base64-encoded file chunks from the source file.
- A Notehub.io [Web Request Route](https://dev.blues.io/reference/notecard-walkthrough/web-transactions/#web-transactions) that points to the `python-file-server` Lambda function.

**Note: This sample applies to linux-based SBCs only. CircuitPython & MicroPython MCUs cannot use this approach.**

Once all of the above a configured, you can run the sample.

1. Add a directory to your Pi and copy the contents of [the application folder](application/) into that directory. _This sample uses a BME680 for sending sample notes. Modify it for your own application before running._
2. Run `pip install -r requirements.txt` to install all of the prerequisites.
3. Run `chmod a+x main.py` to allow `main.py` to reload itself after it loads an updated file.
4. Run `python3 src/main.py`
5. Upload a modified version of `version.py` or `main.py` and watch the console. You'll see something like the following.

![File Downloader Example](/assets/downloader-example.png)

## Sample Application Flow

1. A `.py` file is uploaded to an S3 bucket.
2. The bucket triggers a Lambda function which uses the Notehub API to send an inbound Note to the Notecard.
3. The Notecard detects the inbound Note and fires the `ATTN` pin.
4. The Host (Raspberry Pi) detects the `ATTN` pin is `HIGH` and performs a `web.get` request against an endpoint that is running another Lambda function.
5. The function retrieves the file from S3 and performs a base64 encoding on the contents. That base64 string is returned as a payload to the Notecard. The function breaks files larger than 250 bytes into chunks and can be pinged multiple times to retrieve the entire file.
6. If multiple calls are needed to retrieve the entire file, `web.get` is called until the file has been downloaded.
7. Once all chunks are retrieved, they are combined, decode into UTF-8 text and saved to disk.
8. Finally, the main python program file reloads itself and runs with updated source.