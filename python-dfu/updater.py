

##from __future__ import annotations
from abc import ABC, abstractmethod
from mimetypes import init
from utarfile import TarExtractor

DEFAULT_DFU_MODE_ENTRY_TIMEOUT_SECS = 120


def _defaultRestartFunction()->None:
    raise NotImplementedError

def _defaultStatusReporter(message=None, percentComplete=None)->None:
    pass

class Updater:
    _state = None
    _dfuReader = None
    _inProgress = False
    def __init__(self, dfuReader = None, initialState = None, getTimeMS = lambda :0, fileOpener=None, fileCloser=None, restartFcn=_defaultRestartFunction, statusReporter = _defaultStatusReporter) -> None:
        
        self._dfuReader = dfuReader
        self._getTimeMS = getTimeMS
        self._fileOpener = fileOpener
        self._fileCloser = fileCloser
        self._statusReporter  = statusReporter
        self.RestartFcn = restartFcn

        self.SourceName = None
        self.SourceLength = 0

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
        pass

    def exit(self) -> None:
        pass

    def enter(self) -> None:
        pass


class DFUError(DFUState):

    def __init__(self, message="") -> None:
        self.message = message
        self.Description = "Error: " + message

    def enter(self) -> None:
        self._context._inProgress = False
        
    def execute(self) -> None:
        pass


class CheckForUpdate(DFUState):
    Description = "check for updates"
    def execute(self) -> None:
        isAvailable = self._context._dfuReader.IsUpdateAvailable()
        if isAvailable:
            self._context.transition_to(GetDFUInfo())

class GetDFUInfo(DFUState):
    Description = "get update info"
    def execute(self) -> None:
        info = self._context._dfuReader.GetInfo()

        self._context.SourceName = info["source"]
        self._context.SourceLength = info["length"]

        self._context.transition_to(EnterDFUMode())


class EnterDFUMode(DFUState):
    def execute(self):
        self._context._dfuReader._requestDfuModeEntry()
        self._context.transition_to(WaitForDFUMode())


class ExitDFUMode(DFUState):
    def execute(self):
        self._context._dfuReader._requestDfuModeExit()
        self._context.transition_to(UntarFile())


class WaitForDFUMode(DFUState):
    Description = "wait to enable update"
    def __init__(self, timeoutPeriodSecs=DEFAULT_DFU_MODE_ENTRY_TIMEOUT_SECS) -> None:
        self.TimeoutPeriodSecs = timeoutPeriodSecs
        self._timeoutExpiry = 0

    def execute(self) -> None:

        if self._timeoutExpiry == 0:
            self._timeoutExpiry = self._context._getTimeMS() + self.TimeoutPeriodSecs*1000

        elif self._context._getTimeMS() > self._timeoutExpiry:
            self._context.transition_to(
                DFUError("Timeout waiting for DFU Mode"))
            return

        isDFUMode = self._context._dfuReader._requestDfuModeStatus()

        if isDFUMode:
            self._context.transition_to(MigrateBytesToFile())
            return


class MigrateBytesToFile(DFUState):
    _numBytesWritten = 0
    _length = 0
    Description = "migrate update"
    def enter(self) -> None:
        self._numBytesWritten = 0
        self._length = self._context.SourceLength
        self._context._dfuReader.seek(0)
        self.context._dfuReader._length = self._length

        if self._context._fileOpener is None:
            return

        self._filePointer = self._context._fileOpener(self._context.SourceName, 'wb')

    def exit(self) -> None:

        # if self._context._fileCloser is None:
        #     return

        #self._context._fileCloser(self._filePointer)
        self._filePointer.close()

    def execute(self) -> None:

        if self._numBytesWritten == self._length:
            isValid = self._context._dfuReader.check_hash()
            if isValid:
                self._context.transition_to(ExitDFUMode())
                return

            self._context.transition_to(DFUError())
            return

        n = self._context._dfuReader.read_to_writer(self._filePointer)

        self._numBytesWritten += n

        #self._context._statusUpdater("??", int(self._numBytesWritten *100 / self._length))


class UntarFile(DFUState):
    Description = "extract update files"
    _extractor = TarExtractor()
    def enter(self)-> None:
        self._extractor.openFile(self._context.SourceName)

    def execute(self) -> None:
        try:
            hasMore = self._extractor.extractNext()
        except:
            self._context.transition_to(DFUError(message="TAR extraction failed"))
            return

        if hasMore:
            return

        self._context.transition_to(Install())

class Install(DFUState):
    Description = "install update"
    def execute(self)->None:
        self._context.transition_to(Restart())


class Restart(DFUState):
    Description = "system restart "
    def execute(self)->None:
        self._context._inProgress = False
        self._context.RestartFcn()


