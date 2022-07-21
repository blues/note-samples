from logging.handlers import DEFAULT_UDP_LOGGING_PORT
from multiprocessing import context
#from turtle import up
from unittest.mock import patch, MagicMock
import pytest

from dfu.updater import Updater, DFUState, CheckForUpdate, CheckWatchdogRequirement, GetDFUInfo, EnterDFUMode, ExitDFUMode, WaitForDFUMode, MigrateBytesToFile, UntarFile, Install, Restart, DFUError


def test_Updater_constructor_set_properties():

    card = MagicMock()
    u = Updater(card)

    assert u.Card == card

    s = MagicMock()
    u = Updater(card, initialState=s)

    assert u._state == s

    t = MagicMock()
    u = Updater(card, getTimeMS = t)

    assert u._getTimeMS == t


    u = Updater(card)
    assert u.SourceName == None
    assert u.SourceLength == 0
    assert u.SourceHash == None
    assert u.SuppressWatchdog == True
    assert u._useWatchdog == False

    r = MagicMock()
    u = Updater(card, restartFcn = r)
    assert u.RestartFcn == r

    r = MagicMock()
    u = Updater(card, statusReporter = r)
    assert u._statusReporter == r

    u = Updater(card)
    assert u.InProgress == False

    u = Updater(card, suppressWatchdog = False)
    assert u.SuppressWatchdog == False
    assert u._useWatchdog == False


    


def test_transition_to_none_to_state_from_argument():
    u = Updater(MagicMock())
    assert u._state is None

    s = MagicMock()

    u.transition_to(s)

    assert u._state == s
    assert u._state._context == u


def test_transition_to_state_is_none():
    s = MagicMock()
    u = Updater(MagicMock(), initialState=s)
    assert u._state is not None

    u.transition_to()

    assert u._state is None


def test_transition_from_initial_state_to_new_state():
    s1 = MagicMock()
    s2 = MagicMock()
    u = Updater(MagicMock(), initialState=s1)

    u.transition_to(s2)

    assert u._state == s2
    assert u._state._context == u


def test_transition_to_calls_exit_before_applying_new_state():
    s1 = MagicMock(spec=DFUState)
    u = Updater(MagicMock(), initialState=s1)

    u.transition_to(None)

    s1.exit.assert_called_once()
    assert u._state is None


def test_transition_to_calls_enter():
    s1 = MagicMock(spec=DFUState)
    u = Updater(MagicMock(), initialState=None)

    u.transition_to(s1)

    s1.enter.assert_called_once()


def test_transition_to_calls_enter_after_applying_new_state_context():
    class TestState(DFUState):
        def execute(self) -> None:
            pass

        def enter(self) -> None:
            assert hasattr(self, '_context')
            assert self._context is not None
    
    u = Updater(MagicMock(), initialState=None)

    u.transition_to(TestState())

    
def test_transition_to_calls_statusReporter_on_stateChange():
    
    d = "my description"
    class TestState(DFUState):
        Description = d
        def execute(self) -> None:
            pass

    r = MagicMock()
    u = Updater(MagicMock(), initialState=None, statusReporter = r)

    u.transition_to(TestState())

    r.assert_called_once_with(d)



def test_execute_state_is_none_throws_no_exceptions():
    u = Updater(MagicMock(), initialState=None)
    u.execute()


def test_execute_state_execute_method_is_called_once():
    s = MagicMock()
    u = Updater(MagicMock(),initialState=s)

    u.execute()

    s.execute.assert_called_once()

def test_start_transitions_to_CheckForUpdate():
    u = Updater(MagicMock())
    u.start()
    assert isinstance(u._state, CheckForUpdate)

def test_default_restart_function_errors_on_execution():
    u = Updater(MagicMock())

    with pytest.raises(NotImplementedError):
        u.RestartFcn()


def test_DFUState_context_set():
    c = MagicMock()
    class DFUStateWrapper(DFUState):
        def execute(self):
            pass

    s = DFUStateWrapper()
    s.context = c

    assert s.context == c


def test_CheckForUpdate_is_a_DFUState_class():
    s = CheckForUpdate()
    assert isinstance(s, DFUState)

@patch("dfu.dfu.isUpdateAvailable")
def test_CheckForUpdate_execute_callsDFUReader_IsUpdateAvailable(mock_isAvailable):
    s = CheckForUpdate()
    card = MagicMock()
    mock_isAvailable.return_value = False

    u = Updater(card, initialState=s)

    s.execute()

    mock_isAvailable.assert_called_once_with(card)

def test_CheckForUpdate_execute_noUpdate_doesNotTransitionStates():
    s = CheckForUpdate()
    r = MagicMock()
    r.IsUpdateAvailable.return_value = False

    u = Updater(MagicMock(), initialState=s)

    s.execute()

    assert u._state == s

@patch("dfu.dfu.isUpdateAvailable")
def test_CheckForUpdate_execute_hasUpdate_transitionsToGetInfo(mock_isAvailable):
    s = CheckForUpdate()
    mock_isAvailable.return_value = True

    u = Updater(MagicMock(), initialState=s)

    s.execute()

    assert isinstance(u._state, GetDFUInfo)


@patch("dfu.dfu.isUpdateAvailable")
def test_CheckForUpdate_execute_hasUpdate_transitionsTo_CheckWatchdogRequirement_if_watchdog_not_suppressed(mock_isAvailable):
    s = CheckForUpdate()
    mock_isAvailable.return_value = True

    u = Updater(MagicMock(), initialState=s, suppressWatchdog = False)

    s.execute()

    assert isinstance(u._state, CheckWatchdogRequirement)


def test_CheckWatchdogRequirement_is_a_DFUState_class():
    s = CheckWatchdogRequirement()
    assert isinstance(s, DFUState)

def test_CheckWatchdogRequirement_enter_transitions_to_GETDFUINFO_if_watchdog_is_suppressed():

    s = CheckWatchdogRequirement()
    u = Updater(MagicMock(), suppressWatchdog = True)

    s._context = u

    s.enter()

    assert isinstance(u._state, GetDFUInfo)

def test_CheckWatchdogRequirement_enter_still_in_CheckWatchdogRequirement_if_watchdog_is_not_suppressed():

    s = CheckWatchdogRequirement()
    u = Updater(MagicMock(), suppressWatchdog = False)

    s.context = u
    u._state = s

    s.enter()

    assert isinstance(u._state, CheckWatchdogRequirement)


@patch("dfu.dfu.isWatchdogRequired")
def test_CheckWatchdogRequirement_execute_setsUpdaterUseWatchdogFlag(mock_isRequired):

    mock_isRequired.return_value = True
    s = CheckWatchdogRequirement()
    u = Updater(MagicMock(), suppressWatchdog = False, initialState=s)

    s.execute()

    assert u._useWatchdog == True


    mock_isRequired.return_value = False
    s = CheckWatchdogRequirement()
    u = Updater(MagicMock(), suppressWatchdog = False, initialState=s)

    s.execute()

    assert u._useWatchdog == False


@patch("dfu.dfu.isWatchdogRequired")
def test_CheckWatchdogRequirement_execute_transitions_to_GETDFUINFO(mock_isRequired):

    mock_isRequired.return_value = False
    s = CheckWatchdogRequirement()
    u = Updater(MagicMock(), suppressWatchdog = False, initialState=s)

    s.execute()

    assert isinstance(u._state, GetDFUInfo)




def test_EnterDFUMode_is_a_DFUState_class():
    s = EnterDFUMode()
    assert isinstance(s, DFUState)

@patch("dfu.dfu.enterDFUMode")
def test_EnterDFUMode_execute_callsDfuModeEntryRequest_transitionsToWaitForDFUMode(mock_enterDFU):
    s = EnterDFUMode()
    card = MagicMock()
    u = Updater(card, initialState=s)

    s.execute()

    mock_enterDFU.assert_called_once_with(card)
    assert isinstance(u._state, WaitForDFUMode)


def test_WaitForDFUMode_constructor_sets_properties():
    w = WaitForDFUMode()
    assert w.TimeoutPeriodSecs == 120
    assert w._timeoutExpiry == 0

    timeOutPeriodSecs = 11
    w = WaitForDFUMode(timeoutPeriodSecs=timeOutPeriodSecs)

    assert w.TimeoutPeriodSecs == timeOutPeriodSecs

@patch("dfu.dfu.isDFUModeActive")
def test_WaitForDFUMode_execute_callsDfuModeStatusRequest_ifNotTimedOut(mock_isActive):
    mock_isActive.return_value = False
    w = WaitForDFUMode()
    w._timeoutExpiry = 2
    def getExpiredTime(): return 1

    card = MagicMock()
    u = Updater(card, initialState=w, getTimeMS=getExpiredTime)

    w.execute()

    mock_isActive.assert_called_once_with(card)


@patch("builtins.open")
def test_WaitForDFUMode_execute_transitionsToMigrateBytes_ifInDFUMode(mock_open):
    w = WaitForDFUMode()

    u = Updater(MagicMock(), initialState=w)
    u.SourceName = 'abc'

    w.execute()

    assert isinstance(u._state, MigrateBytesToFile)


def test_WaitForDFUMode_execute_migratesToError_ifTimeoutHasExpired():
    w = WaitForDFUMode()
    w._timeoutExpiry = 1
    def getExpiredTime(): return 2

    u = Updater(MagicMock(),initialState=w, getTimeMS=getExpiredTime)

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



@patch("builtins.open", create=True)
def test_MigrateBytesToFile_enter_populatesProperties(mock_open):
    m = MigrateBytesToFile()
    m._numBytesWritten = 17
    m._length = 19

    card = MagicMock()
    u = Updater(card)
    u.SourceName = 'abc'
    u.SourceLength = 13
    u.SourceHash = 'def'

    m._context = u

    m.enter()

    assert m._numBytesWritten == 0
    assert m._length == u.SourceLength
    assert m._filename == 'abc'
    assert m._reader.NCard == card
    assert m._reader._length == u.SourceLength
    assert m._reader._imageHash == 'def'
    mock_open.assert_called_once_with('abc', 'wb')





@patch("builtins.open")
def test_MigrateBytesToFile_opensFileOnStateEntry_closesFileOnStateExit(mock_open):

        sourceName = 'my_file'
        

        u = Updater(MagicMock())
        u.SourceName = sourceName

        m = MigrateBytesToFile()
        m._context = u

        m.enter()
        mock_open.assert_called_once_with(sourceName, 'wb')

        m.exit()
        m._filePointer.close.assert_called_once()


def test_MigrateBytesToFile_exitsStateWithoutErrorIfNoFileOpened():

       
        m = MigrateBytesToFile()
       
        assert m._filePointer is None
       
        m.exit()
       


def test_MigrateBytesToFile_execute_callsDfuReadWriter():
    u = Updater(MagicMock())

    fp = MagicMock()
    r = MagicMock()
    
    m = MigrateBytesToFile()
    m._length = 1

    m._context = u
    m._filePointer = fp
    m._reader = r

    m.execute()

    r.read_to_writer.assert_called_once_with(fp)


def test_MigrateBytesToFile_execute_incrementsBytesWritten():
    bytesWritten = 13
    initialBytesWritten = 17
    m = MigrateBytesToFile()
    m._numBytesWritten = initialBytesWritten
    m._length = 1

    r = MagicMock()
    r.read_to_writer.return_value = bytesWritten

    u = Updater(MagicMock())
    m._context = u
    m._filePointer = MagicMock()
    m._reader = r

    m.execute()

    assert m._numBytesWritten == bytesWritten + initialBytesWritten


def test_MigrateBytesToFile_execute_allBytesWritten_transitionToExitDFUMode():
    n = 17
    m = MigrateBytesToFile()
    m._length = n
    m._numBytesWritten = n

    r = MagicMock()
    r.check_hash.return_value = True
    u = Updater(MagicMock())
    m._context = u
    m._filePointer = MagicMock()
    m._reader = r

    m.execute()

    assert isinstance(u._state, ExitDFUMode)


def test_MigrateBytesToFile_execute_allBytesWritten_hashCheckFails_transitionToDFUError():
    n = 17
    m = MigrateBytesToFile()
    m._length = n
    m._numBytesWritten = n

    r = MagicMock()
    r.check_hash.return_value = False
    
    u = Updater(MagicMock())
    m._context = u
    m._filePointer = MagicMock()
    m._reader = r

    m.execute()

    assert isinstance(u._state, DFUError)
    assert u._state.discardImage is True

def test_MigrateBytesToFile_execute_callsProgressReporterWithPercentCompletion():
    bytesWritten = 7
    initialBytesWritten = 13
    totalImageBytes = 31
    m = MigrateBytesToFile()
    m._numBytesWritten = initialBytesWritten
    m._length = totalImageBytes


    r = MagicMock()
    r.read_to_writer.return_value = bytesWritten

    p = MagicMock()
    u = Updater(MagicMock(),statusReporter = p)

    m._context = u
    m._filePointer = MagicMock()
    m._reader = r


    m.execute()

    expectedPercentComplete = int((bytesWritten + initialBytesWritten)*100/totalImageBytes)
    p.assert_called_once_with("Migration progress", expectedPercentComplete)

def test_DFUError_isa_DFUState_class():
    e = DFUError()
    assert isinstance(e, DFUState)


def test_DFUError_constructor_sets_properties():
    e = DFUError()
    assert e.message is ""
    assert e.discardImage is False

    m = "my error message"
    e = DFUError(m)
    assert e.message == m

    e = DFUError(discardImage=True)
    assert e.discardImage is True

    e = DFUError(discardImage=False)
    assert e.discardImage is False



def test_DFUError_enter_sets_updater_InProgress_to_False():
    s = DFUError()
    u = Updater(MagicMock(), initialState=s)
    u._inProgress = True

    s.enter()

    assert u.InProgress == False

@patch("dfu.dfu.exitDFUMode")
def test_DFUError_execute_exits_DFUMode(mock_exit):
    card = MagicMock()
    u = Updater(card)

    s = DFUError()
    s.context = u

    s.execute()

    mock_exit.assert_called_once_with(card)


@patch("dfu.dfu.setUpdateError")
@patch("dfu.dfu.exitDFUMode")
def test_DFUError_marksDFUAsFailed_if_discardImage_set(mock_exit, mock_setError):
    card = MagicMock()
    u = Updater(card)

    m = "some error message"
    s = DFUError(m, discardImage=True)
    s.context = u

    s.execute()

    mock_exit.assert_called_once_with(card)
    mock_setError.assert_called_once_with(card, m)

@patch("dfu.dfu.setUpdateError")
@patch("dfu.dfu.exitDFUMode")
def test_DFUError_doesNoteMarksDFUAsFailed_if_discardImage_set_false(mock_exit, mock_setError):
    card = MagicMock()
    u = Updater(card)

    m = "some error message"
    s = DFUError(m, discardImage=False)
    s.context = u

    s.execute()

    mock_exit.assert_called_once_with(card)
    mock_setError.assert_not_called()

@patch("dfu.dfu.exitDFUMode")
def test_DFUError_transitions_to_CheckForUpdate(mock_exit):
    card = MagicMock()

    s = DFUError()
    u = Updater(card, initialState=s)


    s.execute()

    assert isinstance(u._state, CheckForUpdate)

def test_GetDFUInfo_isa_DFUState_class():
    i = GetDFUInfo()
    assert isinstance(i, DFUState)

@patch("dfu.dfu.getUpdateInfo")
def test_GetDFUInfo_execute_requestsAndStoresDFUInfo(mock_getInfo):
    sourceName = "abc"
    length = 13
    md5 = 'def'
    s = GetDFUInfo()

    mock_getInfo.return_value = {"source":sourceName,"length":length,"md5":md5}
    card = MagicMock()
    u = Updater(card, initialState=s)

    s.execute()

    mock_getInfo.assert_called_once_with(card)

    assert u.SourceName == sourceName
    assert u.SourceLength == length
    assert u.SourceHash == md5

@patch("dfu.dfu.getUpdateInfo")
def test_GetDFUInfo_execute_transitions_to_EnterDFUMode(mock_getInfo):
    r = MagicMock()
    mock_getInfo.return_value = {"source":"filename","length":7,"md5":"fake-hash-value"}
    s = GetDFUInfo()
    u = Updater(MagicMock(), initialState=s)

    s.execute()

    assert isinstance(u._state, EnterDFUMode)

    

def test_ExitDFUMode_isa_DFUState_class():
    e = ExitDFUMode()
    assert isinstance(e, DFUState)

@patch("dfu.dfu.exitDFUMode")
def test_ExitDFUMode_execute_callsDfuModeExitRequest(mock_exitDFU):
    s = ExitDFUMode()
    card = MagicMock()
    u = Updater(card, initialState=s)

    s.execute()

    mock_exitDFU.assert_called_once_with(card)
    

def test_ExitDFUMode_execute_transitionsTo_UntarFile():
    s = ExitDFUMode()
    u = Updater(MagicMock(), initialState=s)

    s.execute()

    assert isinstance(u._state, UntarFile)


def test_UntarFile_isa_DFUState_class():
    s = UntarFile()
    assert isinstance(s, DFUState)



def test_UntarFile_enter_establishesTarfileExtractor():
    s = UntarFile()
    s._extractor = MagicMock()
    u = Updater(MagicMock(),)
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

    u = Updater(MagicMock(),initialState=s)

    s.execute()

    assert isinstance(u._state, Install)

def test_UntarFile_execute_errors_transitionTo_ErrorState():
    s = UntarFile()

    def extractNextSideEffect():
        raise(Exception("execution error"))

    e = MagicMock()
    s._extractor = e

    e.extractNext.side_effect = extractNextSideEffect

    u = Updater(MagicMock(),initialState=s)

    s.execute()

    assert isinstance(u._state, DFUError)
    assert u._state.discardImage is True
    




def test_Install_isa_DFUState_class():
    s = Install()
    assert isinstance(s, DFUState)


@patch("dfu.dfu.setUpdateDone")
def test_Install_execute_transitionsTo_Restart(mock_setDone):
    s = Install()
    u = Updater(MagicMock(),initialState=s)
    s.execute()

    assert isinstance(u._state, Restart)

@patch("dfu.dfu.setUpdateDone")
def test_Install_exit_setsDfuProcessToDone(mock_setDone):
    card = MagicMock()
    u = Updater(card)

    s = Install()
    s.context = u

    s.exit()

    mock_setDone.assert_called_once_with(card, "installation complete")



def test_Restart_isa_DFUState_class():
    s = Restart()
    assert isinstance(s, DFUState)

def test_Restart_execute_calls_statemachine_restart_function():
    s = Restart()
    r = MagicMock()
    u = Updater(MagicMock(),initialState=s, restartFcn = r)

    s.execute()

    r.assert_called_once()

def test_Restart_execute_setsUpdaterInprogressToFalse():
    s = Restart()
    r = MagicMock()
    u = Updater(MagicMock(),initialState=s, restartFcn = r)
    u._inProgress = True

    s.execute()

    assert u.InProgress == False
    