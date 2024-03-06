

import notehub
import dfu
import logging
import time


def firmwareUpdate(token, projectUID, fwFile, deviceUID, firmwareType = "user", notes = "", logFolder = ".logs", auditLogFormat = dfu.AuditLogFormatVersion.V1, dryRun = False):

    if firmwareType == "user":
        um = dfu.HostUpdateManager
        versionInfoField = 'HostVersionStr'
    elif firmwareType == "card":
        um = dfu.NotecardUpdateManager
        versionInfoField = 'NotecardVersionStr'
    else:
        raise(Exception(f"Unknown firmware type {firmwareType} selected"))
    
    

    ## Configure logging
    logLevel = logging.INFO
    logging.basicConfig(
        level=logLevel,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(f'{logFolder}/{time.strftime("%Y%m%d-%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )

    ENABLE_UPDATE = False if dryRun else True

    project = notehub.NotehubProject(project_uid=projectUID, user_access_token=token)



    deviceManager = notehub.ProjectDeviceManager(project)

    devices = deviceManager.fetchDevice(deviceUID=deviceUID)
    rpt = []
    for d in devices:
        v = getattr(d, versionInfoField)
        m = um(d)
        m.requestUpdateToImage(fwFile, notes=notes)


        isSuccess = True
        isSkipped = True
        if ENABLE_UPDATE:
            isSkipped = False
            try:
                deviceManager.updateDevice(m.device)    
                
            except:
                isSuccess = False
            
        message = f"{d.UID}:: {v} --> {fwFile}"
        
        if isSuccess and isSkipped:
            logging.info(f"SKIPPED - {message}")
        elif isSuccess:
            logging.info(message)
        else:
            logging.error(f"FAILED - {message}")
        
        rpt.append({"device":d.UID, "current_version": v, "requested_image": fwFile, "success":isSuccess, "skipped": isSkipped})

    report = {"project":projectUID, "devices":deviceUID,"info":rpt}
    logging.info(f"REPORT: {report}")

    return report


