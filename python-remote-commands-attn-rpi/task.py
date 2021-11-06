from multiprocessing import RLock

class TaskQueue():
    _TaskList = [] 
    _Mutex = RLock()

    def hasNext(self) -> bool:
        with self._Mutex:
            return len(self._TaskList) > 0

    def Next(self) -> tuple:
        with self._Mutex:
            t = self._TaskList.pop(0) if self.hasNext() else None
            return t

    def Add(self, fn, arg):
        with self._Mutex:
            self._TaskList.append((fn, arg))

    def _execute_task(self, t):
        f = t[0]
        a = t[1]
        f(*a)

    def ExecuteNext(self):
        with self._Mutex:
            t = self.Next()
            self._execute_task(t)

    def ExecuteAll(self):
        with self._Mutex:
            while self.hasNext():
                t = self.Next()
                self._execute_task(t)