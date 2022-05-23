


##from __future__ import annotations
from abc import ABC, abstractmethod
from mimetypes import init

DEFAULT_DFU_MODE_ENTRY_TIMEOUT_SECS = 120


class Updater:
    _state = None
    _dfuReader = None
    def __init__(self, dfuReader = None, initialState = None, getTimeMS = lambda :0, fileOpener=None, fileCloser=None) -> None:
        
        self._dfuReader = dfuReader
        self._getTimeMS = getTimeMS
        self._fileOpener = fileOpener
        self._fileCloser = fileCloser

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
        self._state.enter()

    def execute(self) -> None:
        if self._state is None:
            return

        self._state.execute()
        


class DFUState(ABC):
    @property
    def context(self) -> Updater:
        return self._context

    @context.setter
    def context(self, context) -> None:
        self._context = context

    @abstractmethod
    def execute(self) -> None:
        pass

    def exit(self) ->None:
        pass

    def enter(self) -> None:
        pass



class DFUError(DFUState):

    def __init__(self, message="") -> None:
        self.message = message

    def execute(self) -> None:
        pass

class GetDFUInfo(DFUState):
    
    def execute(self) -> None:
        info = self._context._dfuReader.GetInfo()

        self._context.SourceName = info["source"]
        self._context.SourceLength = info["length"]


class EnterDFUMode(DFUState):
    def execute(self):
        self._context._dfuReader._requestDfuModeEntry()
        self._context.transition_to(WaitForDFUMode())


class ExitDFUMode(DFUState):
    def execute(self):
        self._context._dfuReader._requestDfuModeExit()
        self._context.transition_to(UntarFile())


class WaitForDFUMode(DFUState):

    def __init__(self, timeoutPeriodSecs=DEFAULT_DFU_MODE_ENTRY_TIMEOUT_SECS) -> None:
        self.TimeoutPeriodSecs = timeoutPeriodSecs
        self._timeoutExpiry = 0

    def execute(self) -> None:

        if self._timeoutExpiry == 0:
            self._timeoutExpiry = self._context._getTimeMS() + self.TimeoutPeriodSecs

        elif self._context._getTimeMS() > self._timeoutExpiry:
            self._context.transition_to(DFUError("Timeout waiting for DFU Mode"))
            return

        isDFUMode = self._context._dfuReader._requestDfuModeStatus()

        if isDFUMode:
            self._context.transition_to(MigrateBytesToFile())
            return
        


class MigrateBytesToFile(DFUState):
    _numBytesWritten = 0
    _length = 0
    
    def enter(self) -> None:
        self._numBytesWritten = 0
        self._length = self._context.SourceLength
        self._context._dfuReader.seek(0)

        if self._context._fileOpener is None:
            return

        self._filePointer = self._context._fileOpener(self._context.SourceName)


    def exit(self) -> None:

        if self._context._fileCloser is None:
            return

        self._context._fileCloser(self._filePointer)

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

    def execute(self) -> None:
        pass