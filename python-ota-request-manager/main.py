



from dfu import AuditLogFormatVersion, DFUType
from firmwareUpdate import firmwareUpdate
import argparse

parser=argparse.ArgumentParser(description="Firmware Update script")
parser.add_argument("-t", "--token",required=True, type=str)
parser.add_argument("-p", "--project",required=True, type=str)
parser.add_argument("-f", "--file", required=True, type=str)
parser.add_argument("-w", "--firmware-type", default = DFUType.User)
parser.add_argument("-a", "--audit-format", default=AuditLogFormatVersion.V1)
parser.add_argument("-d", "--devices", nargs='+')
parser.add_argument("-n", "--notes", default="")
parser.add_argument("-x", "--dryrun", action='store_true')
parser.add_argument("-l", "--logfolder", default=".logs")

args = parser.parse_args()



logFolder = args.logfolder
dryRun = True if args.dryrun else False
token = args.token
projectUID = args.project
fwFile = args.file
deviceUID = args.devices
notes = args.notes
firmwareType = args.firmware_type
auditLogFormat = args.audit_format

report = firmwareUpdate(token, projectUID, fwFile, deviceUID, firmwareType=firmwareType, notes=notes, logFolder=logFolder, auditLogFormat=auditLogFormat, dryRun=dryRun)
