import attn
from unittest.mock import Mock, patch
import pytest


def test_ArmAttn():
    c = Mock()
    c.Transaction.return_value={}

    attn.Arm(c)

    c.Transaction.assert_called_once_with({"req":"card.attn","mode":"rearm"})

def test_DisarmAttn():
    c = Mock()
    c.Transaction.return_value={}

    attn.Disarm(c)

    c.Transaction.assert_called_once_with({"req":"card.attn","mode":"disarm"})


def test_Initialize():
    c = Mock()
    c.Transaction.return_value = {}

    attn.Initialize(c)

    assert c.Transaction.call_count == 3
    assert c.Transaction.call_args_list[0][0][0] == {"req":"card.attn","mode":"disarm"}
    assert c.Transaction.call_args_list[1][0][0] == {"req":"card.attn","mode":"files","files":["commands.qi"]}
    assert c.Transaction.call_args_list[2][0][0] == {"req":"card.attn","mode":"rearm"}


def test_QueryTriggerSource_noTrigger():
    c = Mock()
    c.Transaction.return_value = {}

    s = attn.QueryTriggerSource(c)

    c.Transaction.assert_called_once_with({"req":"card.attn"})
    assert s == {}

def test_QueryTriggerSource_fileTrigger():
    c = Mock()
    c.Transaction.return_value = {"files":["a","b"]}

    s = attn.QueryTriggerSource(c)

    assert s == {"files":["a","b"]}


@patch('attn.ReadCommands')
def test_ProcessAttnInfo_noInfo(rcMock):
    info = {}
    card = Mock()
    card.Transaction.return_value={}
    attn.ProcessAttnInfo(card, info)
    rcMock.assert_not_called()


@patch('attn.ReadCommands')
def test_ProcessAttnInfo_fileInfo(rcMock):
    info = {"files":["commands.qi"]}
    card = Mock()
    attn.ProcessAttnInfo(card, info)

    rcMock.assert_called_once_with(card)

@patch('attn.ReadCommands')
def test_ProcessAttnInfo_moreThanOneFile(rcMock):
    info = {"files":["commands.qi", "anotherfile.db"]}
    card = Mock()
    attn.ProcessAttnInfo(card, info)

    rcMock.assert_called_once_with(card)


@patch('attn.ReadCommands')
def test_ProcessAttnInfo_defaultInfoArg(rcMock):
    card = Mock()
    card.Transaction.return_value = {"files":["anotherfile.qi"]}
    attn.ProcessAttnInfo(card)

    card.Transaction.assert_called_once_with({"req":"card.attn"})

@patch('attn.ReadCommands')
def test_ProcessAttnInfo_noCommandFile(rcMock):
    info = {"files":["anotherfile.qi"]}
    card = Mock()
    attn.ProcessAttnInfo(card, info)

    rcMock.assert_not_called()

@patch('attn.CM')
def test_ReadCommands_noCommands(cm):
    card = Mock()
    card.Transaction.return_value = {"err":" {note-noexist} "}

    attn.ReadCommands(card)

    cm.Enqueue.assert_not_called()
    card.Transaction.assert_called_once_with({"req":"note.get","file":"commands.qi","delete":True})

@patch('attn.CM')
def test_ReadCommands_oneCommandOneStringArg(cm):
    card = Mock()
    card.Transaction.side_effect = [{"body":{"print":"abc"}},
                                    {"err":" {note-noexist} "}]

    attn.ReadCommands(card)

    cm.Enqueue.assert_called_once_with("print",("abc",))
    assert card.Transaction.call_count == 2

@patch('attn.CM')
def test_ReadCommands_oneCommandDictArg(cm):
    card = Mock()
    card.Transaction.side_effect = [{"body":{"count":{"min":1,"inc":3,"max":7}}},
                                    {"err":" {note-noexist} "}]

    attn.ReadCommands(card)

    cm.Enqueue.assert_called_once_with("count",({"min":1,"inc":3,"max":7},))
    assert card.Transaction.call_count == 2

@patch('attn.CM')
def test_ReadCommands_oneCommandMultipleArgs(cm):
    card = Mock()
    card.Transaction.side_effect = [{"body":{"func":["arg1","arg2"]}},
                                    {"err":" {note-noexist} "}]

    attn.ReadCommands(card)

    cm.Enqueue.assert_called_once_with("func",("arg1","arg2"))
    assert card.Transaction.call_count == 2

@patch('attn.CM')
def test_ReadCommands_multipleCommandsMultipleArgs(cm):
    card = Mock()
    card.Transaction.side_effect = [{"body":{"func1":["arg1","arg2"],"func2":"arg3"}},
                                    {"err":" {note-noexist} "}]

    attn.ReadCommands(card)

    callList = cm.Enqueue.call_args_list
    assert callList[0].args == ("func1",("arg1","arg2"))
    assert callList[1].args == ("func2",("arg3",))
    assert card.Transaction.call_count == 2

@patch('attn.CM')
def test_ReadCommands_errThatsNotEndOfQueue(cm):
    card = Mock()
    card.Transaction.return_value = {"err":"error message that does NOT represent end of queue"}

    with pytest.raises(Exception, match="error message that does NOT represent end of queue"):
        attn.ReadCommands(card)

    cm.Enqueue.assert_not_called()


@patch('attn.CM')
def test_ReadCommands_noNoteBody(cm):
    card = Mock()
    card.Transaction.side_effect = [{"field":"value"},
                                    {"err":" {note-noexist} "}]


    attn.ReadCommands(card)

    cm.Enqueue.assert_not_called()
    assert card.Transaction.call_count == 2
