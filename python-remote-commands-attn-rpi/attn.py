#notecard specific ATTN requests and processing
from command import Commands

CM = Commands

remoteCommandQueue = "commands.qi"

def isEndOfQueueErr(e):
    return str.__contains__(e, "{note-noexist}")

def _extractAndEnqueueCommands(body):
    for c in body.items():
        command = c[0]
        args = tuple(c[1]) if isinstance(c[1],list) else (c[1],)
        CM.Enqueue(command, args)


def ReadCommands(card):
    req = {"req":"note.get","file":remoteCommandQueue,"delete":True}

    while True:
        rsp = card.Transaction(req)
        if "err" in rsp:
            if isEndOfQueueErr(rsp["err"]): return
            raise Exception(rsp["err"])

        if "body" not in rsp:
            continue

        body = rsp["body"]
        _extractAndEnqueueCommands(body)




def Arm(card) -> None:
    req = {"req":"card.attn","mode":"rearm"}
    card.Transaction(req)

def Disarm(card) -> None:
    req = {"req":"card.attn","mode":"disarm"}
    card.Transaction(req)

def Initialize(card) -> None:
    Disarm(card)

    req = {"req":"card.attn","mode":"files","files":[remoteCommandQueue]}
    card.Transaction(req)

    Arm(card)

def QueryTriggerSource(card) -> dict:
    req = {"req":"card.attn"}
    return card.Transaction(req)

def ProcessAttnInfo(card, info=None) -> None:
    if not info:
        info = QueryTriggerSource(card)
    
    if "files" in info: 
        files = info["files"]
        if remoteCommandQueue in files: ReadCommands(card)