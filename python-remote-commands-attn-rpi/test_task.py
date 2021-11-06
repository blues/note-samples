from unittest.mock import Mock, patch

import task


def test_constructor_hasDefaultProperties():
    t = task.TaskQueue()
    assert t is not None
    assert len(t._TaskList) == 0

def test_hasNext_noTasksInQueue():
    t = task.TaskQueue()
    assert not t.hasNext()

def test_hasNext_oneTaskInQueue():
    t = task.TaskQueue()
    t._TaskList = [('abc',)]

    assert t.hasNext()

    

def test_hasNext_LocksMutex():
    m = Mock()

    m.__enter__ = Mock()
    m.__exit__ = Mock()
    t = task.TaskQueue()
    t._Mutex = m

    t.hasNext()

    m.__enter__.assert_called_once()
    m.__exit__.assert_called_once()

def test_Next_noTasksInQueue():
    t = task.TaskQueue()
    assert t.Next() is None

def test_Next_oneTaskInQueue():
    t = task.TaskQueue()
    a = ('abc',)
    t._TaskList = [a]

    n = t.Next()

    assert n == a
    assert not t.hasNext()

def test_Next_twoTasksInQueue():
    t = task.TaskQueue()
    a = ('abc',)
    b = ('def',)
    t._TaskList = [a, b]

    n = t.Next()

    assert n == a
    assert t.hasNext()

def test_Next_LocksMutex():
    m = Mock()

    m.__enter__ = Mock()
    m.__exit__ = Mock()
    t = task.TaskQueue()
    t._Mutex = m
    t._TaskList = [('abc',)]
    t.Next()

    m.__enter__.assert_called()
    m.__exit__.assert_called()


def test_Add_noExistingTasks():
    t = task.TaskQueue()
    f = lambda x: x
    a = ('abc',)

    t.Add(f, a)

    assert t.hasNext()
    assert t._TaskList[0] == (f, a)

def test_Add_oneExistingTask():
    t = task.TaskQueue()
    t._TaskList = [('def')]
    f = lambda x:x
    a = ('abc',)

    t.Add(f, a)

    assert t._TaskList[1] == (f,a)

def test_Add_LocksMutex():
    m = Mock()

    m.__enter__ = Mock()
    m.__exit__ = Mock()
    t = task.TaskQueue()
    t._Mutex = m
    
    t.Add(lambda x:x, ('abc',))

    m.__enter__.assert_called_once()
    m.__exit__.assert_called_once()


def test_ExecuteNext_LocksMutex():
    t = task.TaskQueue()
    

    m = Mock()
    m.__enter__ = Mock()
    m.__exit__ = Mock()
    t._Mutex = m
    
    t.ExecuteNext()

    m.__enter__.assert_called()
    m.__exit__.assert_called()

def test_ExecuteNext_oneExistingTask():
    t = task.TaskQueue()
    
    f = Mock()
    a = ('a','b')
    t._TaskList = [(f, a)]

    t.ExecuteNext()

    f.assert_called_once_with('a','b')
    assert not t.hasNext()


def test_ExecuteAll_oneExistingTask():
    t = task.TaskQueue()
    
    f = Mock()
    a = ('a','b')
    t._TaskList = [(f, a)]

    t.ExecuteAll()

    f.assert_called_once_with('a','b')
    assert not t.hasNext()


def test_ExecuteAll_twoExistingTasks():
    t = task.TaskQueue()
    
    f = Mock()
    a = ('a','b')
    t._TaskList = [(f, a),(f,a)]
    numTasks = len(t._TaskList)

    t.ExecuteAll()

    f.assert_called_with('a','b')
    assert f.call_count == numTasks
    assert not t.hasNext()




