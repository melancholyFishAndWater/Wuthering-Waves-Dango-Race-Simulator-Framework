from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Optional
if TYPE_CHECKING:
    from logging import Logger
    from gameEvent import GameEvent
    from character import Character
    from type.status import status
    from game import GameCompatible
from type.Signal import SkillTrigger
import copy, random

game: GameCompatible
_status: status
logger: Logger
GLOBAL_IMPORT = False

class Skill:
    # 检测技能
    def check(self, event: GameEvent, player: Character) -> bool:
        """
        检测技能是否可用发动

        Args:
            event (GameEvent): 检测事件
            player (Character): 检测玩家

        Returns:
            bool: 是否发动
        """
        trigger = self.trigger
        if (trigger is None):
            logger.warning(f"技能{self}的trigger为空")
        elif(
            (trigger.player is not None and trigger.player == event.name and event.player == player) or
            (trigger.target is not None and trigger.target == event.name and player in event.targets) or
            (trigger._global is not None and trigger._global == event.name)
        ):
            return self.filter(event, player)       # TODO
        return False
        
# 其他
    def copy(self) -> "Skill":
        return copy.copy(self)
    def deepcopy(self) -> "Skill":
        return copy.deepcopy(self)

    def __get_init_filter(self, filter: bool | float | Callable) -> Callable[[GameEvent, Character], bool]:
        """
        初始化filter，强制变为函数

        Args:
            filter (None | bool | float | Callable[[GameEvent], bool]): 传入的filter

        Returns:
            Callable[[GameEvent], bool]: 函数
        """
        self.__filter = filter
        if (filter is None): 
            return lambda e, p: False
        elif (isinstance(filter, bool)): 
            return lambda e, p: self.__filter # type: ignore
        elif (isinstance(filter, float)):
            return lambda e, p: random.random() <= self.__filter # type: ignore
        elif callable(filter):
            f: Callable[[GameEvent, Character], None]       # FEAT 感觉还可以优化
            match filter.__code__.co_argcount:
                case 0:
                    f = lambda e, p: filter()
                case 1:
                    f = lambda e, p: filter(e)
                case 2:
                    f = lambda e, p: filter(e, p)
                case _:
                    logger.warning("不允许的filter")
                    if __debug__:
                        raise ValueError()
                    return lambda e, p: False
            return f
        else:
            logger.warning("在初始化技能时，遇到了意外的filter")
            if __debug__:
                raise ValueError()
            return lambda e, p: False

    def __get_init_content(self, content: int | Callable | None) -> Callable[[GameEvent, Character], None]:
        """
        初始化contert，强制变为函数

        Args:
            content (int | Callable): 传入的content

        Returns:
            Callable[[GameEvent, Character], None]: 函数
        """
        if not content:
            return lambda e, p: None
        elif (isinstance(content, int)):
            self.__content = content
            def con(e: GameEvent, p: Character):
                    if e.num is None:
                        assert not __debug__
                        logger.warning("尝试对num==None相加")
                    else: 
                        e.num += self.__content
            return con
        elif callable(content):
            f: Callable[[GameEvent, Character], None]       # FEAT 感觉还可以优化
            match content.__code__.co_argcount:
                case 0:
                    f = lambda e, p: content()
                case 1:
                    f = lambda e, p: content(e)
                case 2:
                    f = lambda e, p: content(e, p)
                case _:
                    logger.warning("不允许的content")
                    if __debug__:
                        raise ValueError()
                    return lambda e, p: None
            return f
        else:
            logger.warning("在初始化技能时，遇到了意外的content")
            if __debug__:
                raise ValueError()
            return lambda e, p: None

    def __str__(self) -> str:
        return f">>>{self.name}"

    """
    技能
    
    技能包括：
    技能生效时机、技能生效条件、技能生效对象、技能生效效果
    
    其他非强制初始化属性：
    名字、描述、目标、所有者
    
    使用Role.appSkill添加技能时，如果目标和所有者为None，会自动设为自身

    Args:
        trigger (Trigger): 生效时机，用于判断是否生效，Trigger.No为不生效
        filter (float, Callable[[Data], None]): 生效条件。float为生效概率，取值为0~1.0；bool为是否触发；可以填函数以判断。如果不满足则结束判断，否则将变量代入effect
        content (int | Callable[["EventData"], "Role | None"] | None): 生效效果。int为移动步数，填函数自行更改传入数据，填None为无效果，需要后续自行设置。
            其返回值Role暂时无实际作用，目前是为了方便类型检查
        target (Role): 生效目标，不填则为自身
        name (str): 技能名，不填则为技能id
        skill_info (str): 技能描述
    """
    def __init__(self, 
                 trigger: Optional[SkillTrigger] = None,
                 filter: bool | float | Callable[[], bool] | Callable[[GameEvent], bool] | Callable[[GameEvent, Character], bool] = False,
                 content: int | Callable[[]] | Callable[[GameEvent]] | Callable[[GameEvent, Character]] = lambda e, p: None,
                 name: str | None = None,
                 info = "",
                 logSkill = True) -> None:
        """
        技能
        
        想要发动技能，至少要这些参数：trigger、filter、content
        
        技能的优先级是非常高的，即使事件取消，只要到达时机也能触发
        
        不过准确来说，只有触发技能才会事件取消吧，虽然现在还没有取消函数，而是用结束标志来代替

        Args:
            trigger (Optional[SkillTrigger], optional): 技能触发时机. Defaults to None.
            filter (bool | float | Callable[[], bool] | Callable[[GameEvent], bool] | Callable[[GameEvent, Character], bool], optional): 过滤条件. Defaults to False.
            content (int | Callable[[]] | Callable[[GameEvent]] | Callable[[GameEvent, Character]]): 技能效果. Defaults to lambdae.
            name (str | None, optional): 技能名字，如果不填，默认为技能id. Defaults to None.
            info (str, optional): 技能描述. Defaults to "".
            logSkill (bool, optional): 是否显示发动技能，一般临时技能用. Defaults to True.
        """        
        if not GLOBAL_IMPORT:
            from game import game as g, _status as s, logger as l
            global game, _status, logger
            game, _status, logger = g, s, l
        self.id = id(self)
        self.name = str(self.id) if not name else name
        self.trigger: SkillTrigger = trigger if trigger else SkillTrigger()
        self.filter = self.__get_init_filter(filter)
        self.content = self.__get_init_content(content)
        self.skill_info = info
        self.logSkill = logSkill      # 是否在日志中显示技能
        
