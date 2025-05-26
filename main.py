from globals import *
from module import Role, Skill, EventProcessor, EventData, EventTrigger


if __name__ == "__main__":
    
    # times = 10
    # times = 50
    # times = 1000
    times = 10000
    
    ep = EventProcessor(23)
    ep.addPhoebe()
    ep.addZaNi()
    ep.addBrant()
    ep.addRoccia()
    
    # a = ep.debugRun()
    # print(ep.resultToNameDict(ep.run()))
    a = ep.runs(times)
    r = ep.resultsToProbability(a, times)
    ep.exampleOutput(r)
