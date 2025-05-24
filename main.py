from globals import *
from module import Role, Skill, EventProcessor, EventData, EventTrigger


if __name__ == "__main__":
    startTime = time.time()
    
    # times = 10
    # times = 50
    # times = 1000
    times = 10000
    
    data = EventData()
    data.setLength(24)
    
    ep = EventProcessor(data)
    ep.addExampleRole1()
    ep.addExampleRole2()
    ep.addExampleRole3()
    ep.addExampleRole4()
    
    a = ep.runs(times)
    r = ep.resultsToProbability(a, times)
    ep.exampleOutput(r)
    
    endTime = time.time()
    print(f"模拟次数：{times}\n模拟时间：{endTime - startTime}秒")
