from datetime import datetime
from dfutypes import DFUType
import json

class DeviceCache:
    TAG_SEPARATOR = "\n"
    TAGS_ENVIRONMENT_VAR = "_tags"
    COMMENTS_ENVIRONMENT_VAR = "_comment"
    SERIAL_NUMBER_ENVIRONMENT_VAR = "_sn"
    
    def __init__(self, uid = None, deviceJSON = {}) -> None:
        self._uid = uid
        self._device_json = deviceJSON
        self._environment_vars_cache = {}
        self._environment_vars = {}
        

    def setEnvironmentVariablesFromJSON(self, envJSON):
        if 'environment_variables' in envJSON:
            envJSON = envJSON['environment_variables']

        self._environment_vars_cache = envJSON
        self._environment_vars = envJSON.copy()

    def getEnv(self, name=None, returnType=None):

        if name is None:
            return self._environment_vars
        
        v = self._environment_vars.get(name, None)

        if returnType and v is not None:
            return returnType(v)
        
        return v

    def deleteEnv(self, name):
        self._environment_vars.pop(name, None)
    
    def setEnv(self, name, value):
        
        self._environment_vars[name] = str(value)

    def getDFUInfo(self, dfuType="card"):
        validTypes = list(DFUType.__dict__.values())
        if dfuType not in validTypes:
            raise(Exception("Selected DFU Type is not valid. Must be a member of DFUType"))
        
        return self._device_json.get('dfu', {}).get(dfuType)
    
    def getVersionStr(self, versionType):
         
        if versionType == DFUType.Card:
          v = self._device_json.get('dfu',{}).get('card',{}).get('version')
          if isinstance(v, str):
            j = json.loads(v)
            return j.get('version')
          return v

        if versionType == DFUType.User:
            return self._device_json.get('dfu',{}).get('user',{}).get('version')
        

    @property
    def EnvironmentVarsIsChanged(self):

        cachedKeys = set(self._environment_vars_cache.keys())
        keys = set(self._environment_vars.keys())

        if cachedKeys != keys:
            return True

        for k in keys:
            if self._environment_vars_cache[k] != str(self._environment_vars[k]):
                return True
            
        return False


    @property
    def UID(self):
        if self._uid:
            return self._uid
        
        return self._device_json['uid']

    @property
    def SerialNumber(self):
        sn = self.getEnv('_sn')

        if sn is not None:
            return sn

        return self._device_json.get('serial_number', None)
    

    
    @SerialNumber.setter
    def SerialNumber(self, value):
        if value == self.SerialNumber:
            return
        
        self.setEnv("_sn", value)

    @property
    def SerialNumberIsChanged(self):
        oldSN = self._environment_vars_cache.get(self.SERIAL_NUMBER_ENVIRONMENT_VAR, None)
        if oldSN is None:
            oldSN = self._device_json.get('serial_number', None)

        return oldSN != self.SerialNumber

    @property
    def Tags(self):
        tags = self.getEnv(self.TAGS_ENVIRONMENT_VAR)
        if tags is None:
            return set()
        listOfTags = tags.split("\n")
        listOfTags = [s.strip() for s in listOfTags]
        listOfTags = list(filter(None, listOfTags))
        return set(listOfTags)
    
    @Tags.setter
    def Tags(self, value):
        if isinstance(value, str):
            value = [value]

        if not isinstance(value, set):
            value = set(value)
        
        value = sorted(value)
        v = self.TAG_SEPARATOR.join(value)
        self.setEnv(self.TAGS_ENVIRONMENT_VAR, v)

    def addTags(self, tags):
        if isinstance(tags, str):
            tags = [tags]
        t = self.Tags
        t.update(tags)
        self.Tags = t

    def removeTags(self, tags):
        if isinstance(tags, str):
            tags = [tags]
        
        t = self.Tags

        for i in tags:
            t.discard(i)

        self.Tags = t

    @property
    def Comments(self):
        return self._environment_vars.get(self.COMMENTS_ENVIRONMENT_VAR, None)
    
    @Comments.setter
    def Comments(self, value):
        self._environment_vars[self.COMMENTS_ENVIRONMENT_VAR] = value

    @property
    def ProvisionedDate(self):
        if 'provisioned' not in self._device_json:
            return
        
        return datetime.fromisoformat(self._device_json['provisioned'])

    @property
    def IsProvisioned(self):
        
        return 'provisioned' in self._device_json
    
    @property
    def NotecardVersionStr(self):
        #v = self._device_json.get('dfu',{}).get('card',{}).get('version', {}).get('version')
        v = self.getVersionStr(DFUType.Card)
        return v
    
    @property
    def HostVersionStr(self):
        #v = self._device_json.get('dfu',{}).get('user',{}).get('version')
        v = self.getVersionStr(DFUType.User)
        return v


    @staticmethod
    def fromV1JSON(json):
        if "devices" not in json:
            return DeviceCache(deviceJSON=json)
        
        return [DeviceCache(deviceJSON=d) for d in json['devices']]
