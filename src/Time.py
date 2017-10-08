from src import Stats

class QueueEntity:
    def __init__(self, entity, ticksLeft=0):
        self.entity = entity
        self.ticksLeft = ticksLeft
        

timeQueue = []


def addToQueue(entity, ticksLeft=0):
    timeQueue.append(QueueEntity(entity, ticksLeft))

    
def removeFromQueue(i):
    del timeQueue[i]


def getNextInQueue():
    tickDownAmount = timeQueue[0].ticksLeft
    for qe in timeQueue:
        qe.ticksLeft -= tickDownAmount
    Stats.ticksProgressed += tickDownAmount
    nextEntity = timeQueue[0].entity
    removeFromQueue(0)
    return nextEntity


def sortQueue():
    timeQueue.sort(key=lambda qe: qe.ticksLeft)
