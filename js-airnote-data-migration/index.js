const NotehubJs = require("@blues-inc/notehub-js");
const plainjs = require("@json2csv/plainjs");
const fs = require("fs");

dataFileName = "data.csv"
eventCacheName = "event_cursor_cache.json";
numEventsPerQuery = 10;


const defaultClient = NotehubJs.ApiClient.instance;

let api_key = defaultClient.authentications["api_key"];
api_key.api_key = process.env.AIRNOTE_PIN

let apiInstance = new NotehubJs.EventApi();

const projectUID = "app:2606f411-dea6-44a0-9743-1130f57d77d8";
const deviceUIDs = ["dev:864475046539952","dev:864475046524855"];

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


csvHeaderArray = parserOpts.fields.map(s => s.replace(/^(body\.)/,""))
csvHeader = csvHeaderArray.join(",") + "\n";

const parser = new plainjs.Parser(parserOpts);

function updateEventCursorCache(device, cursor, fileName = eventCacheName){
    eventCursorCache[device] = cursor;
    console.log(eventCursorCache)
    fs.writeFileSync(fileName, JSON.stringify(eventCursorCache));
}


async function getAirnoteData(deviceUID, cursor="", maxReads = 3){
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
        data = await apiInstance.getProjectEventsByCursor(projectUID, opts);
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




var promises = [];
var csv = "";

deviceUIDs.forEach((d)=>{
    cursor = eventCursorCache[d] || "";
    promises.push(getAirnoteData(d, cursor).then((r) =>{csv += r}))
});

Promise.all(promises)
    .then(()=> {
        fs.writeFileSync(dataFileName,csvHeader)
        fs.appendFileSync(dataFileName, csv)
    })


