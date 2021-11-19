

import command
from unittest.mock import Mock,patch

def test_CommandManager_constructor():
    c = command.CommandManager()

    assert c is not None
    assert c._Catalog == {}
    

def test_IsCommand_NoCommands():
    c = command.CommandManager()
    
    assert not c.IsCommand('dummy_command')

def test_IsCommand_CommandAvailable():
    c = command.CommandManager()
    c._Catalog = {'myCommand':lambda x:x}

    assert c.IsCommand('myCommand')

def test_IsCommand_CommandNotAvailable():
    c = command.CommandManager()
    c._Catalog = {'myCommand':lambda x: x}

    assert not c.IsCommand('dummy_command')

def test_SetSubmitTaskFn():
    c = command.CommandManager()
    f = lambda x:x
    c.SetSubmitTaskFn(f)

    assert c._submitTask == f

def test_GetCommandFn_CommandExists():
    c = command.CommandManager()
    f = lambda x: x
    c._Catalog = {'a': f}

    assert c.GetCommandFn('a') == f

def test_GetCommandFn_CommandNotExist():
    c = command.CommandManager()
    assert c.GetCommandFn('a') is None

def test_Enqueue_CallsTaskEnqueueFunc():
    c = command.CommandManager()
    f = lambda x:x
    c._Catalog = {"func":f}
    a = ('a', 'b')
    c._submitTask = Mock()

    c.Enqueue("func", a)

    c._submitTask.assert_called_once_with(f, a)

def test_Enqueue_NoCommand_TaskNotQueued():
    c = command.CommandManager()
    c._submitTask = Mock()

    c.Enqueue("func",())

    c._submitTask.assert_not_called()


def test_Add():
    c = command.CommandManager()
    f = lambda x:x
    c.Add('my_alias', f)

    assert c._Catalog["my_alias"] == f

def test_AddCommand_OverwritesExisting():
    c = command.CommandManager()
    c._Catalog = {"my_alias":lambda y:y}
    f = lambda x:x
    c.Add('my_alias', f)

    assert c._Catalog["my_alias"] == f

@patch('builtins.print')
def test_printcommand_doesPrint(printMock):
    c = command
    c.Print('hello')

    printMock.assert_called_once_with('hello')

@patch('builtins.print')
def test_countcommand_doesCount(printMock):
    c = command
    c.Count()

    printMock.assert_called_with(10)

@patch('builtins.print')
def test_countcommand_withArgs(printMock):
    c = command
    c.Count({"min":1, "inc":2,"max":4})

    printMock.assert_called_with(3)
    assert printMock.call_count == 2


def test_defaultCommandMap():
    c = command.Commands

    assert c.GetCommandFn('print') == command.Print
    assert c.GetCommandFn('count') == command.Count
    

