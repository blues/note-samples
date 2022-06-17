from logging.handlers import DEFAULT_UDP_LOGGING_PORT
from multiprocessing import context
from turtle import up
from unittest.mock import patch, mock_open, MagicMock

from updater import Updater, DFUState, CheckForUpdate, GetDFUInfo, EnterDFUMode, ExitDFUMode, WaitForDFUMode, MigrateBytesToFile, UntarFile, Install, Restart, DFUError


def test_Updater_constructor_set_properties():
    s = MagicMock()
    u = Updater(initialState=s)

    assert u._state == s

    r = MagicMock()
    u = Updater(dfuReader=r)

    assert u._dfuReader == r

    t = MagicMock()
    u = Updater(getTimeMS=t)

    assert u._getTimeMS == t

    f = MagicMock()
    c = MagicMock()

    u = Updater(fileOpener=f, fileCloser=c)

    assert u._fileOpener == f
    assert u._fileCloser == c

    u = Updater()
    assert u.SourceName == None
    assert u.SourceLength == 0

    r = MagicMock()
    u = Updater(restartFcn = r)
    assert u.RestartFcn == r

    r = MagicMock()
    u = Updater(statusReporter = r)
    assert u._statusReporter == r

    u = Updater()
    assert u.InProgress == False


def test_transition_to_none_to_state_from_argument():
    u = Updater()
    assert u._state is None

    s = MagicMock()

    u.transition_to(s)

    assert u._state == s
    assert u._state._context == u


def test_transition_to_state_is_none():
    s = MagicMock()
    u = Updater(initialState=s)
    assert u._state is not None

    u.transition_to()

    assert u._state is None


def test_transition_from_initial_state_to_new_state():
    s1 = MagicMock()
    s2 = MagicMock()
    u = Updater(initialState=s1)

    u.transition_to(s2)

    assert u._state == s2
    assert u._state._context == u


def test_transition_to_calls_exit_before_applying_new_state():
    s1 = MagicMock(spec=DFUState)
    u = Updater(initialState=s1)

    u.transition_to(None)

    s1.exit.assert_called_once()
    assert u._state is None


def test_transition_to_calls_enter():
    s1 = MagicMock(spec=DFUState)
    u = Updater(initialState=None)

    u.transition_to(s1)

    s1.enter.assert_called_once()


def test_transition_to_calls_enter_after_applying_new_state_context():
    class TestState(DFUState):
        def execute(self) -> None:
            pass

        def enter(self) -> None:
            assert hasattr(self, '_context')
            assert self._context is not None

    u = Updater(initialState=None)

    u.transition_to(TestState())

    
def test_transition_to_calls_statusReporter_on_stateChange():
    
    d = "my description"
    class TestState(DFUState):
        Description = d
        def execute(self) -> None:
            pass

    r = MagicMock()
    u = Updater(initialState=None, statusReporter = r)

    u.transition_to(TestState())

    r.assert_called_once_with(d)



def test_execute_state_is_none_throws_no_exceptions():
    u = Updater(initialState=None)
    u.execute()


def test_execute_state_execute_method_is_called_once():
    s = MagicMock()
    u = Updater(initialState=s)

    u.execute()

    s.execute.assert_called_once()

def test_start_transitions_to_CheckForUpdate():
    u = Updater()
    u.start()
    assert isinstance(u._state, CheckForUpdate)

def test_CheckForUpdate_is_a_DFUState_class():
    s = CheckForUpdate()
    assert isinstance(s, DFUState)

def test_CheckForUpdate_execute_callsDFUReader_IsUpdateAvailable():
    s = CheckForUpdate()
    r = MagicMock()
    r.IsUpdateAvailable.return_value = False

    u = Updater(dfuReader=r, initialState=s)

    s.execute()

    r.IsUpdateAvailable.assert_called_once()

def test_CheckForUpdate_execute_noUpdate_doesNotTransitionStates():
    s = CheckForUpdate()
    r = MagicMock()
    r.IsUpdateAvailable.return_value = False

    u = Updater(dfuReader=r, initialState=s)

    s.execute()

    assert u._state == s

def test_CheckForUpdate_execute_hasUpdate_transitionsToGetInfo():
    s = CheckForUpdate()
    r = MagicMock()
    r.IsUpdateAvailable.return_value = True

    u = Updater(dfuReader=r, initialState=s)

    s.execute()

    assert isinstance(u._state, GetDFUInfo)


def test_EnterDFUMode_is_a_DFUState_class():
    s = EnterDFUMode()
    assert isinstance(s, DFUState)


def test_EnterDFUMode_execute_callsDfuModeEntryRequest_transitionsToWaitForDFUMode():
    s = EnterDFUMode()
    d = MagicMock()
    u = Updater(dfuReader=d, initialState=s)

    s.execute()

    d._requestDfuModeEntry.assert_called_once()
    assert isinstance(u._state, WaitForDFUMode)


def test_WaitForDFUMode_constructor_sets_properties():
    w = WaitForDFUMode()
    assert w.TimeoutPeriodSecs == 120
    assert w._timeoutExpiry == 0

    timeOutPeriodSecs = 11
    w = WaitForDFUMode(timeoutPeriodSecs=timeOutPeriodSecs)

    assert w.TimeoutPeriodSecs == timeOutPeriodSecs


def test_WaitForDFUMode_execute_callsDfuModeStatusRequest_ifNotTimedOut():
    w = WaitForDFUMode()
    w._timeoutExpiry = 2
    def getExpiredTime(): return 1

    d = MagicMock()
    u = Updater(dfuReader=d, initialState=w, getTimeMS=getExpiredTime)

    w.execute()

    d._requestDfuModeStatus.assert_called_once()


def test_WaitForDFUMode_execute_callsDfuModeStatusRequest_ifTimeoutExpiryNotSetYet():
    w = WaitForDFUMode()
    initialExpiry = w._timeoutExpiry
    def getExpiredTime(): return initialExpiry + 1

    d = MagicMock()
    u = Updater(dfuReader=d, initialState=w, getTimeMS=getExpiredTime)

    w.execute()
    assert w._timeoutExpiry == initialExpiry + 1 + w.TimeoutPeriodSecs
    d._requestDfuModeStatus.assert_called_once()


def test_WaitForDFUMode_execute_transitionsToMigrateBytes_ifInDFUMode():
    w = WaitForDFUMode()
    d = MagicMock()
    u = Updater(dfuReader=d, initialState=w)

    w.execute()

    assert isinstance(u._state, MigrateBytesToFile)


def test_WaitForDFUMode_execute_migratesToError_ifTimeoutHasExpired():
    w = WaitForDFUMode()
    w._timeoutExpiry = 1
    def getExpiredTime(): return 2

    u = Updater(initialState=w, getTimeMS=getExpiredTime)

    w.execute()

    assert isinstance(u._state, DFUError)
    assert u._state.message == "Timeout waiting for DFU Mode"


def test_MigrateBytesToFile_isa_DFUState_class():
    m = MigrateBytesToFile()
    assert isinstance(m, DFUState)


def test_MigrateBytesToFile_constructor_populatesProperties():
    m = MigrateBytesToFile()

    assert m._numBytesWritten == 0
    assert m._length == 0


def test_MigrateBytesToFile_enter_populatesProperties():
    m = MigrateBytesToFile()
    m._numBytesWritten = 17
    m._length = 19
    d = MagicMock()
    u = Updater(dfuReader=d)
    u.SourceName = 'abc'
    u.SourceLength = 13

    m._context = u

    m.enter()

    assert m._numBytesWritten == 0
    assert m._length == u.SourceLength


def test_MigrateBytesToFile_enter_goesToStartOfDFUImage():
    m = MigrateBytesToFile()

    d = MagicMock()
    u = Updater(dfuReader=d)
    u.SourceName = 'abc'
    u.SourceLength = 13
    m._context = u

    m.enter()

    d.seek.assert_called_once_with(0)


def test_MigrateBytesToFile_callsFileOpenerOnStateEntry_callsFileCloserOnStateExit():
    sourceName = 'my_file'
    m = MigrateBytesToFile()
    d = MagicMock()
    o = MagicMock()
    c = MagicMock()
    u = Updater(dfuReader=d, fileOpener=o, fileCloser=c)
    u.SourceName = sourceName
    m._context = u

    m.enter()

    o.assert_called_once_with(sourceName)

    m.exit()

    c.assert_called_once()


def test_MigrateBytesToFile_execute_callsDfuReadWriter():
    m = MigrateBytesToFile()
    m._length = 1
    d = MagicMock()
    d.read_to_writer.return_value = 0
    u = Updater(dfuReader=d)
    m._context = u
    m._filePointer = MagicMock()

    m.execute()

    d.read_to_writer.assert_called_once()


def test_MigrateBytesToFile_execute_incrementsBytesWritten():
    bytesWritten = 13
    initialBytesWritten = 17
    m = MigrateBytesToFile()
    m._numBytesWritten = initialBytesWritten
    d = MagicMock()
    d.read_to_writer.return_value = bytesWritten
    u = Updater(dfuReader=d)
    m._context = u
    m._filePointer = MagicMock()

    m.execute()

    assert m._numBytesWritten == bytesWritten + initialBytesWritten


def test_MigrateBytesToFile_execute_allBytesWritten_transitionToExitDFUMode():
    n = 17
    m = MigrateBytesToFile()
    m._length = n
    m._numBytesWritten = n
    d = MagicMock()
    d.check_hash.return_value = True
    u = Updater(dfuReader=d)
    m._context = u
    m._filePointer = MagicMock()

    m.execute()

    assert isinstance(u._state, ExitDFUMode)


def test_MigrateBytesToFile_execute_allBytesWritten_hashCheckFails_transitionToExitDFUMode():
    n = 17
    m = MigrateBytesToFile()
    m._length = n
    m._numBytesWritten = n
    d = MagicMock()
    d.check_hash.return_value = False
    u = Updater(dfuReader=d)
    m._context = u
    m._filePointer = MagicMock()

    m.execute()

    assert isinstance(u._state, DFUError)


def test_DFUError_isa_DFUState_class():
    e = DFUError()
    assert isinstance(e, DFUState)


def test_DFUError_constructor_sets_properties():
    e = DFUError()
    assert e.message == ""

    m = "my error message"
    e = DFUError(m)
    assert e.message == m

def test_DFUError_enter_sets_updater_InProgress_to_False():
    s = DFUError()
    u = Updater(initialState=s)
    u._inProgress = True

    s.enter()

    assert u.InProgress == False



def test_GetDFUInfo_isa_DFUState_class():
    i = GetDFUInfo()
    assert isinstance(i, DFUState)


def test_GetDFUInfo_execute_requestsAndStoresDFUInfo():
    sourceName = "abc"
    length = 13
    i = GetDFUInfo()
    d = MagicMock()
    d.GetInfo.return_value = {"source": sourceName, "length": length}
    u = Updater(dfuReader=d, initialState=i)

    i.execute()

    assert u.SourceName == sourceName
    assert u.SourceLength == length

def test_GetDFUInfo_execute_transitions_to_EnterDFUMode():
    r = MagicMock()
    r.GetInfo.return_value = {"source":"filename","length":7}
    s = GetDFUInfo()
    u = Updater(dfuReader=r, initialState=s)

    s.execute()

    assert isinstance(u._state, EnterDFUMode)

    

def test_ExitDFUMode_isa_DFUState_class():
    e = ExitDFUMode()
    assert isinstance(e, DFUState)


def test_ExitDFUMode_execute_callsDfuModeExitRequest():
    s = ExitDFUMode()
    d = MagicMock()
    u = Updater(dfuReader=d, initialState=s)

    s.execute()

    d._requestDfuModeExit.assert_called_once()


def test_ExitDFUMode_execute_transitionsTo_UntarFile():
    s = ExitDFUMode()
    d = MagicMock()
    u = Updater(dfuReader=d, initialState=s)

    s.execute()

    assert isinstance(u._state, UntarFile)


def test_UntarFile_isa_DFUState_class():
    s = UntarFile()
    assert isinstance(s, DFUState)



def test_UntarFile_enter_establishesTarfileExtractor():
    s = UntarFile()
    s._extractor = MagicMock()
    u = Updater()
    u.SourceName = 'myfile.tar'
    u.transition_to(s)

    s._extractor.openFile.assert_called_once_with('myfile.tar')

def test_UntarFile_execute_untarsNextItem():
    s = UntarFile()
    e = MagicMock()
    s._extractor = e

    e.extractNext.return_value = True

    s.execute()

    e.extractNext.assert_called_once()

def test_UntarFile_execute_noMoreItemsToExtract_transitionsTo_Install():
    s = UntarFile()
    e = MagicMock()
    s._extractor = e

    e.extractNext.return_value = False

    u = Updater(initialState=s)

    s.execute()

    assert isinstance(u._state, Install)

def test_UntarFile_execute_errors_transitionTo_ErrorState():
    s = UntarFile()

    def extractNextSideEffect():
        raise(Exception("execution error"))

    e = MagicMock()
    s._extractor = e

    e.extractNext.side_effect = extractNextSideEffect

    u = Updater(initialState=s)

    s.execute()

    assert isinstance(u._state, DFUError)
    




def test_Install_isa_DFUState_class():
    s = Install()
    assert isinstance(s, DFUState)


def test_Install_execute_transitionsTo_Restart():
    s = Install()
    u = Updater(initialState=s)
    s.execute()

    assert isinstance(u._state, Restart)



def test_Restart_isa_DFUState_class():
    s = Restart()
    assert isinstance(s, DFUState)

def test_Restart_execute_calls_statemachine_restart_function():
    s = Restart()
    r = MagicMock()
    u = Updater(initialState=s, restartFcn = r)

    s.execute()

    r.assert_called_once()

def test_Restart_execute_setsUpdaterInprogressToFalse():
    s = Restart()
    r = MagicMock()
    u = Updater(initialState=s, restartFcn = r)
    u._inProgress = True

    s.execute()

    assert u.InProgress == False
    