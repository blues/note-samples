# Python Firmware Update Overview

```mermaid
sequenceDiagram
    participant User
    participant Notehub
    participant Notecard
    participant Host MCU
    User->>+Notehub: Upload TAR-file
    Host MCU->>+Notecard: Firmware available?
    Notecard->>-Host MCU: No
    User->>+Notehub: Request firmware update
    Notecard->>+Notehub: Sync
    Notehub->>-Notecard: Send firmware info
    loop until transferred
        Notecard->>+Notehub: Requests firmware bytes
        Notehub->>-Notecard: Send firmware bytes
        Notecard->>Notecard: Store firmware bytes
    end
    Notecard->>Notecard: Set "ready" flag
    Notecard->>Notehub: Inform ready for update
    Host MCU->>+Notecard: Firmware available?
    Notecard->>-Host MCU: Yes
    Host MCU->>+Notecard: Request DFU Mode
    Host MCU->>Notecard: Ready?
    Notecard->>Host MCU: No
    Host MCU->>Notecard: Ready?
    Notecard->>Host MCU: Yes
    loop No more bytes
        Host MCU->>+Notecard: Request Bytes
        Notecard->>-Host MCU: Send bytes
        Host MCU->>Host MCU: Store bytes
    end
    Host MCU->>Notecard: Mark migration "Done"
    Notecard->>-Host MCU: Done
    Host MCU->>Host MCU: Untar file
    Notecard->>Notehub: Inform DFU Done
    Host MCU->>Host MCU: Install application
    Host MCU->>Host MCU: Restart application
    Host MCU->>Notecard: Set host MCU firmware version
    Notecard->>Notehub: Host MCU firmware version


``` 
            

**A couple of things:**
* Notecard disables syncing to the cloud when in DFU mode.  
* Upon exiting DFU mode, Notecard will attempt to reconnect to the cloud using the previous "hub" settings
  

