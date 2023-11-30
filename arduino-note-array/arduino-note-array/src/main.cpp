#include <Arduino.h>
// Copyright 2023 Blues Inc.  All rights reserved.
//
// Use of this source code is governed by licenses granted by the
// copyright holder including that found in the LICENSE file.
//
// This example demonstrates how to include multiple data points into the same `note.add` request.
//
// By default, this uses templated notes via the `note.template` API.  There are several advantages, which include
// increasing the available storage on the Notecard, improving data compression on the transfer to the cloud, reducing the time,
// and reducing data consumption to send the data to the Notehub.  The disadvantage is if the structure of the data is changing frequently, then
// the advantages achieved with using `note.template` are diminished.


#include <stdlib.h>

#include <notecard.h>

// Note that both of these definitions are optional; just prefix either line
// with `//` to remove it.
// - Remove txRxPinsSerial if you wired your Notecard using I2C SDA/SCL pins
//   instead of serial RX/TX
// - Remove usbSerial if you don't want the Notecard library to output debug
//   information
#ifdef USE_SERIAL
  // use #define USE_SERIAL or -D USE_SERIAL in the compliation configurations to use UART (serial) communications with Notecard
  // otherwise it will default to I2C 
  #define txRxPinsSerial Serial1
#endif

#ifndef DISABLE_DEBUG
  #define usbSerial Serial
#endif


// This is the unique Product Identifier for your device.  This Product ID tells
// the Notecard what type of device has embedded the Notecard, and by extension
// which vendor or customer is in charge of "managing" it. In order to set this
// value, you must first register with notehub.io and "claim" a unique product
// ID for your device.  It could be something as simple as as your email address
// in reverse, such as "com.gmail.smith.lisa.test-device" or
// "com.outlook.gates.bill.demo"

// This is the unique Product Identifier for your device
#ifndef PRODUCT_UID
#define PRODUCT_UID "" // "com.my-company.my-name:my-project"
#pragma message "PRODUCT_UID is not defined in this example. Please ensure your Notecard has a product identifier set before running this example or define it in code here. More details at https://dev.blues.io/tools-and-sdks/samples/product-uid"
#endif

#define myProductID PRODUCT_UID

#define INVALID_TIME (-1)            // flag returned if Notecard does not have valid time
#define DATA_FILE_NAME ("data.qo")  // Notefile to store data


#define NUM_MEASUREMENTS (30)          // Number of Measurements to gather in a Note    
#define MEASUREMENT_PERIOD_SEC (2)   // Period between Measurements in seconds

#define USE_TEMPLATED_NOTES  // Define to use Templated Notes.  Undefining/commenting this out will remove any existing templates from the Notefile when the code executes.


Notecard notecard;

void configureNotecard(){
  
    J *req = notecard.newRequest("hub.set");
    if (myProductID[0])
    {
        JAddStringToObject(req, "product", myProductID);
    }

    // For the purposes of this example, the Notecard is set to be connected to Notehub continuously
    JAddStringToObject(req, "mode", "continuous");
    JAddBoolToObject(req, "sync", true);

    bool success = notecard.sendRequestWithRetry(req, 5); // 5 seconds

    if (!success){
      notecard.logDebugf("Failed to configure Notecard");
      return;
    }
    notecard.logDebugf("Configuration Complete!");

    return;

}

void configureMeasurementDataTemplate(const char* filename, uint8_t numDataPoints){
   // Create a template Note that we will register. This template note will
    // look "similar" to the Notes that will later be added with note.add, in
    // that the data types are used to intuit what the ultimate field data types
    // will be, and their maximum length.
    //
    // This template is designed to enable storing multiple data points in the same Note.
    // As such, the number of data points must be known a priori to use the note.template API

    J* req = notecard.newRequest("note.template");
    if (req == NULL)
      return; //handle memory allocation error here

    // Register the template in the output queue notefile
    JAddStringToObject(req, "file", filename);

    #ifdef USE_TEMPLATED_NOTES
    J *body = JAddObjectToObject(req, "body");
    if (body == NULL)
      return; // handle memory allocation error here

    J *array = JAddArrayToObject(body, "array");
    if (array == NULL)
      return; // handle memory allocation error here

    for (uint8_t i = 0; i < numDataPoints; i++)
    {
      J* item = JCreateObject();
      JAddNumberToObject(item, "timestamp", TINT64);
      JAddNumberToObject(item, "temperature", TFLOAT32);
      JAddItemToArray(array,item);

    }
    #endif
   
    notecard.sendRequest(req);
}

void sendMeasurementData(const char* filename, J* array){
   
    J* req = notecard.newRequest("note.add");
    if (req == NULL)
      return; //handle memory allocation error here

    // Register the template in the output queue notefile
    JAddStringToObject(req, "file", filename);
    
    J *body = JAddObjectToObject(req, "body");
    if (body == NULL)
      return; // handle memory allocation error here

    JAddItemToObject(body, "array", array);

  notecard.sendRequest(req);
  notecard.sendRequest(notecard.newRequest("hub.sync"));
}

int64_t getTime(){
  int64_t time = INVALID_TIME;
  J* rsp = notecard.requestAndResponse(notecard.newRequest("card.time"));

  if ((rsp != NULL) && (JGetString(rsp, "zone") != "UTC,Unknown"))
    time = int64_t(JGetNumber(rsp, "time"));  // Retrieve valid time

  notecard.deleteResponse(rsp);

  return time;

}

double getTemperature(){
  double temperature = 0;
  J *rsp = notecard.requestAndResponse(notecard.newRequest("card.temp"));
  if (rsp != NULL){
    temperature = JGetNumber(rsp, "value");
    notecard.deleteResponse(rsp);
  }
  
  return temperature;
}

void appendMeasurement(J* array, int64_t time, double temperature){
  J* item = JCreateObject();
  JAddNumberToObject(item, "timestamp", time);
  JAddNumberToObject(item, "temperature", temperature);

  JAddItemToArray(array, item);
}


// One-time Arduino initialization
void setup()
{
    // Set up for debug output (if available).
#ifdef usbSerial
    // If you open Arduino's serial terminal window, you'll be able to watch
    // JSON objects being transferred to and from the Notecard for each request.
    usbSerial.begin(115200);
    const size_t usb_timeout_ms = 3000;
    for (const size_t start_ms = millis(); !usbSerial && (millis() - start_ms) < usb_timeout_ms;)
        ;
    notecard.setDebugOutputStream(usbSerial);
#endif

    // Initialize the physical I/O channel to the Notecard
#ifdef txRxPinsSerial
    notecard.begin(txRxPinsSerial, 9600);
#else
    notecard.begin();
#endif
  notecard.logDebugf("Starting to configure notecard...\n");
  configureNotecard();
  notecard.logDebugf("Starting to configure Template...\n");
  configureMeasurementDataTemplate(DATA_FILE_NAME, (NUM_MEASUREMENTS));
    
  notecard.logDebugf("Ready to GO!!!\n");
   
}


J* JSONArray = JCreateArray();
void loop()
{
    // Count the simulated measurements that we send to the cloud, and stop the
    // demo before long.
    static unsigned count = 0;
    

    int64_t timestamp = getTime();
    if (timestamp == INVALID_TIME)
    {
      notecard.logDebugf("Time is invalid");
      delay(MEASUREMENT_PERIOD_SEC * 1000);
      return;
    }

    double temperature = getTemperature();

    appendMeasurement(JSONArray, timestamp, temperature);

    if (++count > NUM_MEASUREMENTS)
    {
        sendMeasurementData(DATA_FILE_NAME, JSONArray);
        JDelete(JSONArray);
        JSONArray = JCreateArray();

        count = 0;
    }

    delay(MEASUREMENT_PERIOD_SEC * 1000);
    
}