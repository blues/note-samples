import sys
if sys.implementation.name == 'cpython':  # type: ignore
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

    def migrateAndInstall(self, restart=False):
        

        isAvailable = self._dfu.isUpdateAvailable(self._card)
        if not isAvailable:
            self._statusUpdater("No update available", None)
            return
        
        stage = ""
        try:
            stage = "migrate file"
            self._statusUpdater(stage)
            fileName = self.gather()
            stage = "extract update content"
            self._statusUpdater(stage)
            self.extract(fileName)
            stage = "mark update complete"
            self._statusUpdater(stage)
            self._dfu.setUpdateDone(self._card, 'migrated and extracted update')
            
        except Exception as e:
            self._statusUpdater(f"failed to {stage}")
            self._statusUpdater(f"error: {str(e)}")
            self._statusUpdater(f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")
            
            self._dfu.setUpdateError(self._card, f"failed to {stage}")
            return

        if restart:
            stage = "restart"
            self._statusUpdater(stage)
            try:
                self.restart()
            except Exception as e:
                self._statusUpdater(f"failed to {stage}")
                return
        

        
    
    def gather(self) -> str:

        info = self._dfu.getUpdateInfo(self._card)
        if info is None:
            raise Exception("failed to get update info")

        filename = info["source"]

        try:
            with open(filename, "wb") as f: #type: ignore
                p = lambda x:self._statusUpdater("Migrating", x)
                self._dfu.copyImageToWriter(self._card, f, progressUpdater=p)

        except Exception as e:
            self._statusUpdater("Failed to migrate update", None)
            self._dfu.setUpdateError(self._card, 'failed to copy image to file')
            return ""

        self._statusUpdater("Successful copy of update",None)

        return filename

    def extract(self, filename)-> None:
        
        with  open(filename, 'rb') as f: # type: ignore
            t = utar.TarFile(f)
            for i in t:
                if i.Type is utar.Type.DIR:
                    self._writeTarItemAsDir(i)
                    continue
            
                self._writeTarItemToFile(i)


    def _writeTarItemAsDir(self, item):
        os.mkdir(item.Name)

    def _writeTarItemToFile(self, item):
        
        with open(item.Name, "wb") as f: # type: ignore
            buf = bytearray(utar.BLOCK_LENGTH_BYTES)
            for b in item.Blocks:
                numBytes = b.readinto(buf)
                f.write(buf[0:numBytes])



    

    def restart(self) -> None:
        raise NotImplementedError
        


def isUpdateAvailable(card):
    pass


def update(card):
    pass


