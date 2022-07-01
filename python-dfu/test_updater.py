from logging.handlers import DEFAULT_UDP_LOGGING_PORT
from multiprocessing import context
from turtle import up
from unittest.mock import patch, mock_open, MagicMock
import pytest

from updater import Updater, DFUState, CheckForUpdate, GetDFUInfo, EnterDFUMode, ExitDFUMode, WaitForDFUMode, MigrateBytesToFile, UntarFile, Install, Restart, DFUError


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

    r = MagicMock()
    u = Updater(card, restartFcn = r)
    assert u.RestartFcn == r

    r = MagicMock()
    u = Updater(card, statusReporter = r)
    assert u._statusReporter == r

    u = Updater(card)
    assert u.InProgress == False


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

@patch("dfu.isUpdateAvailable")
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

@patch("dfu.isUpdateAvailable")
def test_CheckForUpdate_execute_hasUpdate_transitionsToGetInfo(mock_isAvailable):
    s = CheckForUpdate()
    mock_isAvailable.return_value = True

    u = Updater(MagicMock(), initialState=s)

    s.execute()

    assert isinstance(u._state, GetDFUInfo)


def test_EnterDFUMode_is_a_DFUState_class():
    s = EnterDFUMode()
    assert isinstance(s, DFUState)

@patch("dfu.enterDFUMode")
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

@patch("dfu.isDFUModeActive")
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

    m._context = u

    m.enter()

    assert m._numBytesWritten == 0
    assert m._length == u.SourceLength
    assert m._filename == 'abc'
    assert m._reader.NCard == card
    assert m._reader._length == u.SourceLength
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


def test_MigrateBytesToFile_exitsStateCleanlyIfNoFileOpened():

       
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


def test_MigrateBytesToFile_execute_allBytesWritten_hashCheckFails_transitionToExitDFUMode():
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
    u = Updater(MagicMock(), initialState=s)
    u._inProgress = True

    s.enter()

    assert u.InProgress == False

def test_DFUError_execute_does_not_error():
    s = DFUError()
    s.execute()



def test_GetDFUInfo_isa_DFUState_class():
    i = GetDFUInfo()
    assert isinstance(i, DFUState)

@patch("dfu.getUpdateInfo")
def test_GetDFUInfo_execute_requestsAndStoresDFUInfo(mock_getInfo):
    sourceName = "abc"
    length = 13
    i = GetDFUInfo()

    mock_getInfo.return_value = {"source":sourceName,"length":length}
    card = MagicMock()
    u = Updater(card, initialState=i)

    i.execute()

    mock_getInfo.assert_called_once_with(card)

    assert u.SourceName == sourceName
    assert u.SourceLength == length

@patch("dfu.getUpdateInfo")
def test_GetDFUInfo_execute_transitions_to_EnterDFUMode(mock_getInfo):
    r = MagicMock()
    mock_getInfo.return_value = {"source":"filename","length":7}
    s = GetDFUInfo()
    u = Updater(MagicMock(), initialState=s)

    s.execute()

    assert isinstance(u._state, EnterDFUMode)

    

def test_ExitDFUMode_isa_DFUState_class():
    e = ExitDFUMode()
    assert isinstance(e, DFUState)

@patch("dfu.exitDFUMode")
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
    




def test_Install_isa_DFUState_class():
    s = Install()
    assert isinstance(s, DFUState)


def test_Install_execute_transitionsTo_Restart():
    s = Install()
    u = Updater(MagicMock(),initialState=s)
    s.execute()

    assert isinstance(u._state, Restart)



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
    