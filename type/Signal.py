from typing import Literal, Annotated, Union
# 目前支持的时机，不排除以后会增加，依次是：游戏开始，轮次开始，回合开始，移动前，移动中，移动后，回合结束，游戏结束

# 由event.trigger()发出的时机信号汇总
Signal_Trigger = Literal[
    "gameInit", "gameStart", "gameEnd",
    "roundStart", "roundBegin", "roundEnd",
    "phaseMove", "phaseMoveBefore", "phaseMoveBegin", "Move", "phaseAfter", "phaseMoveEnd", 
    "check",
    "useSkill"
]
# 其他带额外时机的事件
EventWithTrigger = Annotated[str, "应该是这种形式 [skillname]"]
# 额外时机
Signal_Event_ = Literal["Before", "Begin", "After", "End"]
# 派生信号，你看上面变量懂我意思，[]内都是可变的，主要是实在没找到合适的方案
Signal_Event = Annotated[str, "应该是这种形式 [EventWithTrigger][Signal_Event_]"]
# 总信号，自创信号只支持技能的信号
Signal = Union[Signal_Trigger, Signal_Event]

class SkillTrigger():
    """
    技能触发时机
    """
    def __init__(self, 
                 player: Union[Signal, None] = None, 
                 target: Union[Signal, None] = None, 
                 _global: Union[Signal, None] = None) -> None:
        """技能触发时机

        Args:
            player (Union[Signal, None], optional): 技能所有者. Defaults to None.
            target (Union[Signal, None], optional): 技能所有者成为目标时. Defaults to None.
            _global (Union[Signal, None], optional): 进入此时机时。可用于触发一些没有处理角色的时机. Defaults to None.
        """
        self.player = player
        self.target = target
        self._global = _global
