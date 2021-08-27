import requests
import json

rootUrl = 'https://api.notefile.net/v1'
appUid = 'app:2606f411-dea6-44a0-9743-1130f57d77d8'
defaultPageSize = 50
defaultMaxRequests = 1000

def getEventData(pin, deviceId,since=None,pageSize=defaultPageSize):
    if since == None:
        since = ""
    url = f"{rootUrl}/projects/{appUid}/events?deviceUIDs={deviceId}&pageSize={pageSize}&since={since}"

    r = requests.get(url, headers={"content-type":"application/json","X-Session-Token":f"{pin}"})

    return json.loads(r.content)


def migrateAirnoteData(pin, deviceId, migrateFunc=lambda x:None, since=None,pageSize=defaultPageSize,max_requests=defaultMaxRequests):

    hasMore = True
    numRequests = 0
    while hasMore and numRequests < max_requests:
        c = getEventData(pin, deviceId, since=since, pageSize=pageSize)

        if "has_more" not in c:
            return

        hasMore = c.get("has_more")
        
        for e in c["events"]:
            if e["file"] != "_air.qo":
                continue
            migrateFunc(e)

        since = c.get("through")
        numRequests += 1





    