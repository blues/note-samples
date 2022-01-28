import sys
if sys.implementation.name == 'cpython':
    sys.path.append("src")

import os

import dfu
import utarfile as utar

_defaultStatusUpdater = lambda m, p:None

class UpdateManager():

    def __init__(self, card=None, statusUpdater = _defaultStatusUpdater) -> None:
        self._card = card
        self._dfu = dfu
        self._statusUpdater = statusUpdater

    def migrateAndInstall(self, reset=False):
        pass

        # if DFU not available
             # self._statusUpdater("No update available", None)
            # return
        
        # try
          # stage = "migrate file"
          # self._statusUpdater(stage)
          # fileName = self.gather()
          # stage = "extract update content"
          # self._statusUpdater(stage)
          # self.extract(fileName)
          # stage = "mark update complete"
          # self._statusUpdater(stage)
          # self._dfu.setUpdateDone('migrated and extracted update')
          # if reset:
          #   stage = "reset"
          #   self._statusUpdater(stage)
          #   self.restart()
        # except Exception as e:
           # self._statusUpdater(f"Failed to {stage}", None)
           # self._dfu.setUpdateError(self._card, f"failed to {stage}")
           # return

        

        
    
    def gather(self) -> str:

        isAvailable = self._dfu.isUpdateAvailable(self._card)
        if not isAvailable:
            self._statusUpdater("No update available", None)
            return ""
        
        
        info = self._dfu.getUpdateInfo(self._card)
        filename = info["source"]

        try:
            with open(filename, "wb") as f:
                p = lambda x:self._statusUpdater("Migrating", x)
                self._dfu.copyImageToWriter(self._card, f, progressUpdater=p)

        except Exception as e:
            self._statusUpdater("Failed to migrate update", None)
            self._dfu.setUpdateError(self._card, 'failed to copy image to file')
            return ""

        self._statusUpdater("Successful copy of update",None)
        self._dfu.setUpdateDone(self._card, 'copied image to file')

        return filename

    def extract(self, filename)-> None:
        
        with  open(filename, 'rb') as f:
            t = utar.TarFile(f)
            for i in t:
                if i.Type is utar.Type.DIR:
                    self._writeTarItemAsDir(i)
                    continue
            
                self._writeTarItemToFile(i)


    def _writeTarItemAsDir(self, item):
        os.mkdir(item.Name)

    def _writeTarItemToFile(self, item):
        
        with open(item.Name, "wb") as f:
            buf = bytearray(utar.BLOCK_LENGTH_BYTES)
            for b in item.Blocks:
                numBytes = b.readinto(buf)
                f.write(buf[0:numBytes])



    

    def restart(self) -> None:
        pass


def isUpdateAvailable(card):
    pass


def update(card):
    pass


