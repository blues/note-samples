from abc import ABC, abstractmethod
from mimetypes import init
from utarfile import TarExtractor
import dfu


DEFAULT_DFU_MODE_ENTRY_TIMEOUT_SECS = 120


def _defaultRestartFunction()->None:
    raise NotImplementedError

def _defaultStatusReporter(message=None, percentComplete=None)->None:
    pass



class Updater:
    _state = None
    _dfuReader = None
    _inProgress = False
    _useWatchdog = False
    def __init__(self, card, initialState = None, getTimeMS = lambda :0, restartFcn=_defaultRestartFunction, statusReporter = _defaultStatusReporter, suppressWatchdog = True) -> None:
        
        self.Card = card
        self._getTimeMS = getTimeMS
        self._statusReporter  = statusReporter
        self.RestartFcn = restartFcn

        self.SourceName = None
        self.SourceLength = 0
        self.SourceHash = None

        self.SuppressWatchdog = suppressWatchdog

        self.transition_to(initialState)

    def transition_to(self, state=None) -> None:
        if self._state is not None:
            self._state.exit()

        self._state = state

        if self._state is None:
            return

        self._state._context = self
        self._statusReporter(self._state.Description)
        self._state.enter()

    def execute(self) -> None:
        if self._state is None:
            return

        self._state.execute()

    def start(self) -> None:
        self.transition_to(CheckForUpdate())

    @property
    def InProgress(self) -> bool:
        return self._inProgress

        


class DFUState(ABC):
    Description = ""
    @property
    def context(self) -> Updater:
        return self._context

    @context.setter
    def context(self, context) -> None:
        self._context = context

    @abstractmethod
    def execute(self) -> None:
        pass # pragma: no cover

    def exit(self) -> None:
        pass

    def enter(self) -> None:
        pass


class DFUError(DFUState):

    def __init__(self, message="", discardImage=False) -> None:
        self.message = message
        self.Description = "Error: " + message
        self.discardImage = discardImage

    def enter(self) -> None:
        self.context._inProgress = False
        
    def execute(self) -> None:
        dfu.exitDFUMode(self.context.Card)

        if self.discardImage:
            dfu.setUpdateError(self.context.Card, self.message)

        self.context.start()


class CheckForUpdate(DFUState):
    Description = "check for updates"
    def execute(self) -> None:
        isAvailable = dfu.isUpdateAvailable(self.context.Card)
        if isAvailable:
            self.context.transition_to(CheckWatchdogRequirement())

class CheckWatchdogRequirement(DFUState):

    def enter(self) -> None:
        if self.context.SuppressWatchdog:
            self.context.transition_to(GetDFUInfo())

    def execute(self)->None:
        self.context._useWatchdog = dfu.isWatchdogRequired(self.context.Card)

        self._context.transition_to(GetDFUInfo())


class GetDFUInfo(DFUState):
    Description = "get update info"
    def execute(self) -> None:
        info = dfu.getUpdateInfo(self.context.Card)

        self.context.SourceName = info["source"]
        self.context.SourceLength = info["length"]
        self.context.SourceHash = info["md5"]

        self.context.transition_to(EnterDFUMode())


class EnterDFUMode(DFUState):
    def execute(self):
        dfu.enterDFUMode(self.context.Card)
        self.context.transition_to(WaitForDFUMode())


class ExitDFUMode(DFUState):
    def execute(self):
        dfu.exitDFUMode(self.context.Card)
        self.context.transition_to(UntarFile())


class WaitForDFUMode(DFUState):
    Description = "wait to enable update"
    def __init__(self, timeoutPeriodSecs=DEFAULT_DFU_MODE_ENTRY_TIMEOUT_SECS) -> None:
        self.TimeoutPeriodSecs = timeoutPeriodSecs
        self._timeoutExpiry = 0

    def execute(self) -> None:

        if self._timeoutExpiry == 0:
            self._timeoutExpiry = self.context._getTimeMS() + self.TimeoutPeriodSecs*1000

        elif self.context._getTimeMS() > self._timeoutExpiry:
            self.context.transition_to(DFUError("Timeout waiting for DFU Mode"))
            return

        isDFUMode = dfu.isDFUModeActive(self.context.Card)

        if isDFUMode:
            self.context.transition_to(MigrateBytesToFile())
            return


class MigrateBytesToFile(DFUState):
    _numBytesWritten = 0
    _length = 0
    _filename = ''
    _filePointer = None
    Description = "migrate update"
    def enter(self) -> None:
        self._numBytesWritten = 0
        self._length = self.context.SourceLength
        self._filename = self.context.SourceName
        self._hash = self.context.SourceHash
        self._reader = dfu.dfuReader(self.context.Card, info={"length":self._length, "md5":self._hash})

        self._filePointer = open(self._filename, 'wb')

    def exit(self) -> None:
        if self._filePointer is None:
            return

        self._filePointer.close()

    def execute(self) -> None:

        if self._numBytesWritten == self._length:
            isValid = self._reader.check_hash()
            if not isValid:
                self.context.transition_to(DFUError(f"Hash value does not match. Expected {self._reader._imageHash}, computed {self._reader.get_hash()}", discardImage=True))
                return

            self.context.transition_to(ExitDFUMode())
            return

            
        n = self._reader.read_to_writer(self._filePointer)

        self._numBytesWritten += n

        

        self.context._statusReporter("Migration progress", int(self._numBytesWritten *100 / self._length))


class UntarFile(DFUState):
    Description = "extract update files"
    _extractor = TarExtractor()
    def enter(self)-> None:
        self._extractor.openFile(self.context.SourceName)

    def execute(self) -> None:
        try:
            hasMore = self._extractor.extractNext()
        except:
            self.context.transition_to(DFUError(message="TAR extraction failed", discardImage=True))
            return

        if hasMore:
            return

        self.context.transition_to(Install())

class Install(DFUState):
    Description = "install update"
    def execute(self)->None:
        self.context.transition_to(Restart())

    def exit(self)->None:
        dfu.setUpdateDone(self.context.Card, "installation complete")


class Restart(DFUState):
    Description = "system restart "
    def execute(self)->None:
        self.context._inProgress = False
        self.context.RestartFcn()


