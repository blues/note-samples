import sys
import os
if sys.version_info[0]<3:       # require python3
 raise Exception("Python3 required! Current (wrong) version: '%s'" % sys.version_info)

localDir = os.path.dirname(__file__)
sys.path.insert(0, localDir)
from notehubEndpointApp import app as application