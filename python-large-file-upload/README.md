# Python Large File Upload

This sample shows how to use the Notecard to upload a large file using the Notecard Web request API



## Hardware Setup

### PC with Standard OS

| | |
|---|---|
|Notecard Interface Options| {USB, UART}|
|Default Notecard Interface| USB*|
|Platform| Linux/Windows|
|Python version| Python3 |


Notecard USB appears as serial port on PC.  

## Notehub Configuration

| | |
|---|---|
|Product UID|Need this to identify the Notehub project|
|Web Proxy Route|Used by the Notecard Web Request API to relay requests to the desired service|

### Creating Web Proxy Route

1. Navigate to https://notehub.io/projects
2. Select which project you are going to use
3. Click "Routes" from the navigation menu on the left-hand side of the page
4. Click "Create Route" button on the upper right
5. Select "Web Proxy Route"
6. Set the following
   
   |Parameter|Value|Description|
   |---------|-----|-----------|
   |Name|My Web Request Route|Name of route you want to appear in Notehub|
   |URL|https://myjson.live/ping|URL where HTTP requests from Notecard are forwarded|
   |Alias|ping|Identifier used by Notecard to determine which Web Proxy route to apply|

7. Click "Create Route"
   


## Using the Application

### Usage Requirements
 - Product UID from Notehub project
 - Full path to the file you want to upload via Notecard
 - Name of the serial port the Notecard is connected to (Default is COM4)

### Basic Usage

``` bash
> python main.py -u MY_PRODUCT_UID -f MY_FILE_PATH -p COM4
```


### Additional Options

``` bash
> python main.py -h
```

## Application Installation

1. Clone this repository
2. Run `pip install -r requirements.txt` to install all of the prerequisites.
