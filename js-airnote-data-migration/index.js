const NotehubJs = require("@blues-inc/notehub-js");
const plainjs = require("@json2csv/plainjs");
const fs = require("fs");

dataFileName = "data.csv"
eventCacheName = "event_cursor_cache.json";
numEventsPerQuery = 100;
const deviceUIDs = [
    "dev:xxxxxxxxxx",
];

const airnoteProjectUID = "app:2606f411-dea6-44a0-9743-1130f57d77d8";



const defaultClient = NotehubJs.ApiClient.instance;

let api_key = defaultClient.authentications["api_key"];
api_key.api_key = process.env.NOTEHUB_PIN

let apiInstance = new NotehubJs.EventApi();



// Load event cache from file
try {
    content = fs.readFileSync(eventCacheName);
} catch (error) {
    content = "{}";
}
let eventCursorCache = JSON.parse(content);


const parserOpts = {
    header: false,
    fields:[
    "event",
    "device",
    "sn",
    "when",
    "best_lat",
    "best_lon",
    "body.aqi",
    "body.aqi_algorithm",
    "body.aqi_level",
    "body.c00_30",
    "body.c00_50",
    "body.c01_00",
    "body.c02_50",
    "body.c05_00",
    "body.csamples",
    "body.csecs",
    "body.humidity",
    "body.pm01_0",
    "body.pm01_0_rstd",
    "body.pm01_0cf1",
    "body.pm02_5",
    "body.pm02_5_rstd",
    "body.pm02_5cf1",
    "body.pm10_0",
    "body.pm10_0_rstd",
    "body.pm10_0cf1",
    "body.pressure",
    "body.sensor",
    "body.temperature",
    "body.voltage",
]
};

// Create header for CSV File
csvHeaderArray = parserOpts.fields.map(s => s.replace(/^(body\.)/,""))
csvHeader = csvHeaderArray.join(",") + "\n";

const parser = new plainjs.Parser(parserOpts);

//Cache last downloaded event for each device for future reference
function updateEventCursorCache(device, cursor, fileName = eventCacheName){
    eventCursorCache[device] = cursor;
    fs.writeFileSync(fileName, JSON.stringify(eventCursorCache));
}

// Download data from Airnote Project
async function getAirnoteData(deviceUID, cursor="", maxReads = 20){
let opts = {
    limit: numEventsPerQuery, 
    cursor: cursor, 
    sortOrder: "asc", 
    files:"_air.qo",
    deviceUID: deviceUID,
    };

    let csv = ""
    count = 0;
    while (count < maxReads){
        data = await apiInstance.getProjectEventsByCursor(airnoteProjectUID, opts);
        count++;
        csv += parser.parse(data.events) + "\n";
        if (!data.has_more || !data.next_cursor){
            break
        }
        opts.cursor = data.next_cursor;
        
    }
    cursor = (data.events[data.events.length - 1].event) || ""

    updateEventCursorCache(deviceUID,cursor)
    return(csv);

}


async function getAirnoteSensorData(deviceID) {
    const defaultClient = NotehubJs.ApiClient.instance;
    const authKey = defaultClient.authentications["api_key"];
    const apiKey = authKey.api_key = process.env.NOTEHUB_PIN;

    let apiInstance = new NotehubJs.EventApi();

    const airnoteProjectUID = "app:2606f411-dea6-44a0-9743-1130f57d77d8"

    /*
    this gets the start and end date of the desired time range. A function is set up for this
    the calculateTimeRange function receives a range like 'yesterday', 'week', 'month' and
    calculates the starting and ending datetimes. because a UNIX EPOCH timestamp is needed
    for this request, a conversion is made using valueOf().
    
    Example: today being 14/06/2023, a 'yesterday' arguement will produce;
    startDate = 1686096000000 (which is 2023-06-07T00:00:00.000Z)
    endDate = 1686700799999 (which is 2023-06-13T23:59:59.999Z)
    */
    // const [startDate, endDate] = calculateTimeRange(dataRange);
    // console.log(startDate.valueOf() + " " + endDate.valueOf());
    
    const opts = {
        pageSize: 50,
        sortOrder: "asc",
        startDate: Math.floor(1686096000000/1000),
        endDate: Math.ceil(1686700799999/1000),
        files: "_air.qo",
        deviceUID: deviceID,
    };

    // Fetch data from NoteHub
    try {
        const fetchedData = await apiInstance.getProjectEvents(airnoteProjectUID, opts);

        //log to console for debugging purposes
        console.log('Data fetched:', fetchedData);

        // return fetchedData;
    } catch (error) {
        console.log('Error fetching data:', error);
        throw error;
    }
}





var promises = [];
var csv = "";

promises.push(getAirnoteSensorData(deviceUIDs[0]))

// deviceUIDs.forEach((d)=>{
//     cursor = eventCursorCache[d] || "";
//     promises.push(getAirnoteData(d, cursor).then((r) =>{csv += r}))
// });

Promise.all(promises)
    .then(()=> {
        // fs.writeFileSync(dataFileName,csvHeader)
        // fs.appendFileSync(dataFileName, csv)
    })


