import urllib3
from urllib.parse import urlencode
import json
import time
from device import DeviceCache


http = urllib3.PoolManager()

#TODO: Break-out HTTP interactions as Service function or class
# - method that accepts HTTP request info, can encode form data or JSON data, raises exceptions on non 200 responses, encodes results as JSON
# - consider moving OAUTH, _v1Request, _v0Request, header methods, to their own ServiceClass to make testing easier


class NotehubProject:

    _shared_header = {
                'Accept': 'application/json',
                'Content-Type': 'text/plain',
                }

    def __init__(self, project_uid, user_access_token=None, client_id=None, client_secret=None, host='https://api.notefile.net') -> None:

        if user_access_token is None and client_id is None:
            raise(Exception("Must provide either a user access token or a client Id for authentication"))
        
        if client_id is not None and client_secret is None:
            raise(Exception("Must provide a client secret along with the client ID to enable authentication"))
        
        isUserToken = user_access_token is not None
        
        self._project_uid = project_uid
        self.host = host
        self._bearer_token = None
        self._rate_limit_timeout = 0
        self._rate_limit_increment_seconds = 8.60
        
        if isUserToken:
            self.getAuthHeader = self._getXSessionHeader
            self._user_access_token = user_access_token
            return
        
        self._client_id = client_id
        self._client_secret = client_secret
        self.getAuthHeader = self._getOauthTokenHeader
        

    def _bearer_token_is_expired(self):
        return time.time() >= self._bearer_token["expires_at"]
    
    def _query_oauth_for_token(self):
        url = 'https://notehub.io/oauth2/token'
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'client_id': self._client_id,
            'client_secret': self._client_secret
        }

        s = urlencode(data)

        print(s)
        response = http.request("POST", url, headers=headers, body=s)

        responseJSON = json.loads(response.data)

        if response.status == 200:
            return responseJSON
            
        else:
            raise(Exception(f"Unable to get token: {responseJSON}"))


    def _getBearerToken(self):
        if self._bearer_token is None or self._bearer_token_is_expired():
            token_info = self._query_oauth_for_token()
            token_info["expires_at"] = time.time() + token_info["expires_in"]*60

            self._bearer_token = token_info

        return self._bearer_token["access_token"]

            



    def _getOauthTokenHeader(self):
        headers = self._shared_header
        headers["Authorization"] = "Bearer " + self._getBearerToken()

        return headers

    def _getXSessionHeader(self):
        headers = self._shared_header
        headers["X-Session-Token"] = self._user_access_token

        return headers
    
    def _issueRequest(self, method, url, headers, body):
        while time.time() < self._rate_limit_timeout:
            time.sleep(0.1)
        
        self._rate_limit_timeout = time.time() + self._rate_limit_increment_seconds

        response = http.request(method, url, headers=headers, body=body)

        if response.status <200 or response.status >= 300:
            raise(Exception(f"Problem performing Notehub request!\n Status Code: {response.status}\n Message:{response.data}"))
        
        return response
    
    def _v1Request(self, path, payload = {}, params = {}, method = 'GET'):

        p = urlencode(params)
        url = f"{self.host}/v1/projects/{self._project_uid}/{path}?{p}"

        headers = self.getAuthHeader()

        jsonPayload = json.dumps(payload)

        response = self._issueRequest(method, url, headers, jsonPayload);

        if not response.data:
            return {}
        

        return json.loads(response.data)
    
    def _v0Request(self, req, deviceUID = None):
        url = f"{self.host}/req?app={self._project_uid}&device={deviceUID if not deviceUID==None else ''}"
        headers = self.getAuthHeader()

        if isinstance(req, str):
            req = {"req":req}

        body = json.dumps(req)

        response = self._issueRequest('GET', url, headers, body);

        if not response.data:
            return {}
        

        return json.loads(response.data)
    

    def getDeviceInfo(self, deviceUID=None):

        if deviceUID != None:
            if isinstance(deviceUID, str):
                return self._v1Request(f"devices/{deviceUID}")
            
            return [self._v1Request(f"devices/{d}") for d in deviceUID]
        

        hasMore = True
        devices = []
        pageSize = 500
        pageNumber = 1
        while hasMore:
            r = self._v1Request("devices", params={"pageNum": pageNumber, "pageSize": pageSize})
            devices += r["devices"]
            hasMore = r.get("has_more", False)
            pageNumber += 1

        return devices   
        

    
    def provisionDevice(self, deviceUID, productUID):

        self._v1Request(f"devices/{deviceUID}/provision", payload={"product_uid":productUID}, method='POST')

    def deleteDevice(self, deviceUID, purge=False):
        purgeStr = str(purge).lower()
        self._v1Request(f"devices/{deviceUID}", method='DELETE', params={'purge':purgeStr})
    
    def enableDevice(self, deviceUID):
        return self._v1Request(f"devices/{deviceUID}/enable", method='POST')
    
    def disableDevice(self, deviceUID):
        return self._v1Request(f"devices/{deviceUID}/disable", method='POST')
    
    def enableDeviceConnectivityAssurance(self, deviceUID):
        self._v1Request(f"devices/{deviceUID}/enable-connectivity-assurance", method='POST')

    def disableDeviceConnectivityAssurance(self, deviceUID):
        self._v1Request(f"devices/{deviceUID}/disable-connectivity-assurance", method='POST')

    def setDeviceEnvironmentVars(self, deviceUID, environmentVars):
        return self._v1Request(f"devices/{deviceUID}/environment_variables", payload={"environment_variables":environmentVars}, method='PUT')
    
    def getDeviceEnvironmentVars(self, deviceUID, environmentVars=None):
        v = self._v1Request(f"devices/{deviceUID}/environment_variables")
        if environmentVars is None:
            return v
        
        if isinstance(environmentVars, str):
            environmentVars = [environmentVars]

        a = {key: v["environment_variables"][key] for key in environmentVars if key in v["environment_variables"]}
        return a
    
    def getHostFirmwareInfo(self):
        info = self._v0Request({"req":"hub.app.upload.query","type":"firmware"})
        return info['uploads']
    
        


class ProjectDeviceManager:

    def __init__(self, notehubProject) -> None:
        self._project = notehubProject

    def updateDevice(self, device, force=False):
        
        if force or device.EnvironmentVarsIsChanged:
            self._project.setDeviceEnvironmentVars(device.UID, device.getEnv())

    def _fetchSingleDevice(self, deviceUID):
        json = self._project.getDeviceInfo(deviceUID)
        env = self._project.getDeviceEnvironmentVars(deviceUID)
        d = DeviceCache.fromV1JSON(json)
        d.setEnvironmentVariablesFromJSON(env)
        return d

    def fetchDevice(self, deviceUID):
        if isinstance(deviceUID, str):
            return self._fetchSingleDevice(deviceUID)
        
        d = [self._fetchSingleDevice(d) for d in deviceUID]

        return d
    
    


