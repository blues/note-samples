import requests
import json

rootUrl = 'https://api.notefile.net/v1'
appUid = 'app:2606f411-dea6-44a0-9743-1130f57d77d8'
defaultLimit = 50
defaultMaxRequests = 1000

def getEventData(pin, deviceId,cursor="",limit=defaultLimit, files=None):

    if not cursor:
        cursor = ""
        
    if files:
        files = files if isinstance(files, str) else ",".join(files)

    url = f"{rootUrl}/projects/{appUid}/events-cursor?deviceUID={deviceId}&limit={limit}&cursor={cursor}&files={files}"

    r = requests.get(url, headers={"content-type":"application/json","X-Session-Token":f"{pin}"})

    return json.loads(r.content)


def migrateAirnoteData(pin, deviceId, migrateFunc=lambda x:None, cursor=None,limit=defaultLimit,max_requests=defaultMaxRequests):

    hasMore = True
    numRequests = 0
    while hasMore and numRequests < max_requests:
        c = getEventData(pin, deviceId, cursor=cursor, limit=limit, files="_air.qo")

        if "has_more" not in c:
            return

        hasMore = c.get("has_more", False)
        
        for e in c["events"]:
            migrateFunc(e)

        cursor = c.get("next_cursor","")

        numRequests += 1





    