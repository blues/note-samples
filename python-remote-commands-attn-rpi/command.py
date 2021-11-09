
class CommandManager():
    _Catalog = {}
    def __init__(self) -> None:
        self._Catalog = {}

    def _submitTask(self, f, a):
        pass

    def IsCommand(self, id) -> bool:  
        return id in self._Catalog

    def SetSubmitTaskFn(self, f):
        self._submitTask = f

    def GetCommandFn(self, id):
        return self._Catalog[id] if self.IsCommand(id) else None

    def Enqueue(self, id, args):
        if not self.IsCommand(id):
            return
        f = self.GetCommandFn(id)
        self._submitTask(f, args)

    def Add(self, id, fn):
        self._Catalog[id] = fn



def Print(content):
    print(content)

def Count(args={}):
    x = args["min"] if "min" in args else 0
    inc = args["inc"] if "inc" in args else 1
    max = args["max"] if "max" in args else 10
    while x <= max:
        print(x)
        x += inc


Commands = CommandManager()


Commands.Add("print", Print)
Commands.Add("count", Count)