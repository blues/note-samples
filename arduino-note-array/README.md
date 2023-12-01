# Multiple Data Elements in Notecard Note

If you need to route multiple JSON data elements at once, the current best practice is to
accumulate the data elements in a JSON array that is added to the Note `body` field.

It is recommended to use the `note.template` request to created a Templated Note in the Notefile.
This enhances data storage on the Notecard, makes data transfer more efficient, and is transparent
to the downstream cloud services.

## JSON Data Accumulation

In order to use a single `note.add` request to apply accumulated data, it is recommended to use a JSON array to work with Templated Notes

In this example, the measurement loop appends a timestamp and temperature measurement to a CJSON Array.  When the end of the array is reached, then the JSON array content is transferred
to the Notecard using a `note.add` request, and a sync is requested with Notehub to push the data to the cloud.

As described in this example the JSON array is a fixed size, and only submits the data to Notehub when the array has been filled.  As written today, this means the data is susceptible to loss if the host MCU loses power or is reset between storing measurement data in memory, and performing the `note.add` request.

### Note Template Structure

For Templated Notes, the structure must be defined a priori (the template can be updated if the structure changes).

The JSON structure of the Templated Note outlined in this example

```json
 {
    "req":"note.template",  // note.template request
    "file":"data.qo"        // Notefile the template is applied to
    "body":{
        "array":[
            {
                "timestamp": 18,     // 64-bit signed integer
                "temperature": 18.1   // 64-bit floating-point number (double precision)
            },
            {
                "timestamp": 18,
                "temperature": 18.1
            },
            ... // repeated for each member of the array
            {
                "timestamp": 18,
                "temperature": 18.1
            }
        ]
    }
  }

```

### Request Object Deletion on Send

The Arduino Notecard API uses `malloc` by default to construct the JSON object in the heap memory.  

To try and make it easier for the developer to prevent memory leaks in the heap, the `sendRequest`, `requestAndResponse`, and `sendRequestWithRetry` APIs all call the `JDelete` function to clear the request object passed to each of these functions.

That means, the JSON request object must be constructed prior to each call, even if the request object has the same structure.

## Other References

- [Working with Note Templates](https://dev.blues.io/notecard/notecard-walkthrough/low-bandwidth-design/#working-with-note-templates)
- [`note.template` API Guide](https://dev.blues.io/api-reference/notecard-api/note-requests/#note-template)
- [Arduino SDK `note.template` example](https://github.com/blues/note-arduino/blob/master/examples/Example5_UsingTemplates/Example5_UsingTemplates.ino)
