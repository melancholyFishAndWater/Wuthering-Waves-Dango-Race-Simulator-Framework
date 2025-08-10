from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Self

from skill import Skill

if TYPE_CHECKING:
    from game import GameCompatible
    from type.status import status
    from character import Character
    from logging import Logger
import logging
import random
from type.Signal import Signal, Signal_Event_
import time, random

game: GameCompatible
_status: status
logger: Logger
GLOBAL_IMPORT = False

class GameEvent():
    """
    游戏事件
    """
# 调试
    def findAllParent(self) -> list[GameEvent]:
        result = []
        e = self
        while e.parent:
            e = e.parent
            result.append(e)
        return result
    def deFindAllParent(self):
        result = self.findAllParent()
        return list(map(lambda e: e.name, result))
    
    def deFindAllChildEventsNotFinished(self, deep=-1) -> dict[int, list[GameEvent]]:
        """
        递归找到所有未完成的子事件，包括自己
        
        理想情况下，在游戏结束时，所有事件都是完成的

        Args:
            deep (int, optional): 递归深度，不需要自行传递. Defaults to -1.

        Returns:
            dict[int, list[GameEvent]]: 事件，深度: 事件列表
        """
        deep += 1
        result: dict[int, list[GameEvent]] = {}
        if not self._finished:       # 判断自身
            if deep not in result:
                result[deep] = []
            result[deep].append(self)
        for child in self.childEvents:      # 判断子事件
            child_result = child.deFindAllChildEventsNotFinished(deep)
            for d, e in child_result.items():
                if d not in result:
                    result[d] = []
                result[d].extend(e)
        return result
    
    def setPlayer(self, player: str | Character | None):
        """
        设置当前事件处理角色

        Args:
            player (str | Character | None): 角色
        """
        plt = _status.players_info[player] if isinstance(player, str) else player
        if logger.level == logging.NOTSET:
            logger.debug(f"事件{self}尝试将当前操作角色{self.player}改为{plt}")
        if self.player != plt:
            logger.debug(f"事件{self}设置当前操作角色为{plt}")
            self.player = plt
            _status.player = plt

    def getParent(self, level: int | Signal = 1) -> Optional[GameEvent]:
        """
        获取第一个匹配的父事件，默认为获取上一个

        Args:
            level (int | Signal, optional): 事件深度，或名字. Defaults to 1.

        Returns:
            Optional[GameEvent]: 事件
        """
        if isinstance(level, str):
            if not self.parent:
                return
            evt = self
            while evt.parent:
                evt = evt.parent
                if evt.name == level:
                    return evt
            return
        elif isinstance(level, int):
            evt = self
            for i in range(level):
                if evt.parent:
                    evt = evt.parent
                else:
                    return
            return evt

# 主逻辑
    def getResult(self) -> dict[int, str]:
        """
        获得游戏结果

        Returns:
            dict[int, str]: 结果字典
        """
        result = game.atEndPlayers
        return dict(zip(range(1, len(result) + 1), result))

    def check(self) -> None:
        """
        检测是否有技能发动
        """
        logger.debug(f"检测技能")
        next = game.createEvent("check", self)
        self.childEvents.append(next)
        _status.event = next
        for player in game.players:
            player_info = _status.players_info[player]
            result = player_info.check(self)
            for s in result:
                next.skill=s
                next.trigger("useSkill")
        next.skill=None
        next._finished=True
        self.next = None
        _status.event = self
    
    def trigger(self, name: Signal) -> GameEvent:
        """
        触发并开始一个事件
        
        执行完毕此函数后，self.next重置为None，childEvents里会有此事件

        Args:
            name (Signal): 事件名

        Returns:
            GameEvent: 触发的事件
        """
        # FEAT 检测合法性
        nextEvt = game.createEvent(name, self)
        may_list: list[Character | None] = [
            _status.player, 
            self.parent.player if self.parent else None
        ]
        triggerPlt = next((i for i in may_list if i), None)
        nextEvt.setPlayer(triggerPlt)
        nextEvt.start()
        self.next = None
        _status.event = self
        return nextEvt
    
    def waitNext(self) -> None:
        """
        执行事件
        """
        _status.event = self
        self.check()
        if not self._finished:
            logger.debug(f"执行事件{self.name}")
            parent = self.parent
            name = self.name
            if parent:
                if parent.name == "phaseMove":
                    match parent._triggered:
                        case "Before":      # FEAT
                            plt = self.player
                            assert plt
                            num = plt.getMoveNum()      # 投出
                            logger.info(f"{self.player}投出了：{num}")
                            parent.num = num
                        case "Begin":
                            num = self.num
                            # assert self.player and num is not None
                            assert num
                            for i in range(num):
                                self.trigger("Move")
                            logger.info(f"{self.player}一共移动了{self.num}格")
                            # self.player.move(num)
                        case "After":
                            pass
                        case "End":
                            plt = self.player
                            assert plt is not None
                            if plt.cell >= game.cells:
                                plts = [plt] + plt.findAllHeadPlayer()
                                plts.reverse()
                                for i in plts:
                                    logger.info(f"{i}到达了终点")
                                    game.atEndPlayers.append(i.name)
                            else:
                                logger.info(f"{plt}现在在第{plt.cell}格")
                            logger.info(f"{game.getOuts()}")
                        case _:
                            raise ValueError("意外的值：", self.name, self._triggered)
                    self._finished = True
                    return
                elif parent.parent and parent.parent.name == "useSkill":
                    skillName = self.skill
                    assert skillName
                    match parent._triggered:
                        case "Begin":
                            skill = _status.skills_info[skillName]
                            trigger = self.getParent("phaseMove")
                            plt = self.player
                            assert trigger and plt and trigger.next
                            skill.content(trigger.next, plt)
                    self._finished = True
                    return
            if name == "Move":      # 细化的移动
                plt = self.player
                assert plt
                plt.move3()
            elif name == "phaseMove":
                logger.debug(f"{self.player}进入移动回合")
            elif name == "useSkill":
                skillName = self.skill
                if skillName not in _status.skills_info:
                    logger.warning(f"{self.player}尝试发动一个不存在的技能：{name}")
                    if __debug__ or logger.level <= logging.DEBUG:
                        raise ValueError()
                else:
                    skill = _status.skills_info[skillName]
                    if logger.level <= logging.DEBUG:
                        logger.debug(f"{self.player}发动了技能：{skill}")
                    else:
                        logger.info(f"{self.player}发动了技能")
                    self.trigger(skillName)
            elif name == "roundEnd":
                self._phaseMoveOrder = game.phaseMoveOrder
            elif name == "roundBegin":
                logger.info(f"本轮移动顺序：{game.phaseMoveOrder}")
                self._phaseMoveOrder = game.phaseMoveOrder
                while True:
                    order = [i for i in game.phaseMoveOrder if i not in game.atEndPlayers and i not in game.movedPlayers]     # 排除一些角色提前进入了终点或移动过
                    if len(order) == 0:
                        break
                    nextPlt = order[0]
                    _status.player = _status.players_info[nextPlt]
                    self.trigger("phaseMove")
                _status.player = None       # 清空正在操作的角色
            elif name == "roundStart":
                game.roundNumber += 1
                logger.info(f"第{game.roundNumber}轮开始")
                if len(game.movedPlayers) != 0:
                    game.movedPlayers = []
                    order = list(set(game.players) - set(game.atEndPlayers))
                    random.shuffle(order)
                    game.phaseMoveOrder = order.copy()
                else:
                    order = game.phaseMoveOrder
                self._phaseMoveOrder = order.copy()
                logger.debug(f"生成原始移动顺序{order}")
            elif name == "gameStart":
                while True:
                    self.times += 1
                    self.trigger("roundStart")      # NOICE 再这么写都够全部额外时机了
                    self.trigger("roundBegin")
                    self.trigger("roundEnd")
                    if len(game.atEndPlayers) == len(game.players):
                        break
            elif name == "gameInit":
                logger.debug("开始游戏初始化")
                if len(game.players) == 0:
                    logger.warning("没有参与角色，游戏退出")
                else:
                    order = game.players.copy()
                    random.shuffle(order)
                    self._phaseMoveOrder = order.copy()
                    game.phaseMoveOrder = order.copy()
                    root = _status.players_info[order.pop(-1)]      # 给所有角色连起来
                    order.reverse()
                    for plt in order:
                        info = _status.players_info[plt]
                        root.append(info)
                    self.trigger("gameStart")
                    self.trigger("gameEnd")
            elif name == "gameEnd":
                game.log("游戏结束")
            # else:
            #     raise ValueError("意外的值：", self.name, self._triggered)
            self._finished = True
        else:
            logger.debug(f"事件{self}已结束，取消继续执行此事件")

    def loop(self) -> Self:
        """
        loop执行此事件，请不要直接调用它，而是通过start开始事件

        Returns:
            Self: 自身
        """
        if self.name == "phaseMove" or self.name in _status.skills:
            def loop_trigger(to: Signal_Event_):
                self._triggered = to
                self.trigger(self.name + to)
            self.waitNext()
            t = Signal_Event_.__args__
            while self._triggered != t[-1]:
                self.times += 1
                index = t.index(self._triggered) + 1 if self._triggered else 0
                loop_trigger(t[index])
            return self
        else:
            self.waitNext()
            return self

    def start(self) -> Self:
        """
        开始此事件

        Returns:
            Self: 返回loop结束后的事件
        """
        if (self.parent): self.parent.childEvents.append(self)
        _status.event = self
        next = self.loop()
        return next
    
    def __str__(self) -> str:
        return self.name
    
    def __init__(self, 
                 name: Signal, 
                 player: Optional[Character] = None, 
                 target: Optional[Character] = None, 
                 targets: Optional[list[Character]] = None, 
                 num: int | None = None,
                 parent: "GameEvent | None" = None,
                 ) -> None:
        """
        游戏事件，大部分公有成员都允许修改，不要自己使用和修改含下划线变量

        Args:
            name (Signal): 
            player (Optional[Character], optional): 触发角色. Defaults to None.
            target (Optional[Character], optional): 目标角色(列表的第一位). Defaults to None.
            targets (Optional[list[Character]], optional): 目标角色列表. Defaults to None.
            num (int | None, optional): 事件数，如果有的话。默认继承父事件的num. Defaults to None.
            parent (GameEvent | None, optional): 父事件. Defaults to None.
        """
        if not GLOBAL_IMPORT:
            from game import game as g, _status as s, logger as l
            global game, _status, logger
            game, _status, logger = g, s, l
    # 事件链
        self.parent = _status.event if not parent and name != "gameInit" else parent
        self.next: Optional[GameEvent] = None        # 下一个要执行的事件。现在只有调用 createEvent 的时候才会触发，而createEvent目前只有trigger会调用
        self.childEvents: list[GameEvent] = []     # 执行完毕的子事件，只会在调用 event.start 的时候添加
    # 常用args
        self.name: Signal = name
        self.player: Optional[Character] = self.parent.player if not player and self.parent else player     # 默认继承上个事件的处理角色
        self.target = player if target is None else target
        self.targets = [target] if targets is None else targets     # 这两参数都得手动传
        self.num = self.parent.num if self.parent and not num else num
    # FLAG
        self._finished = False       # 事件是否结束
        self._triggered: Optional[Signal_Event_] = None      # 当前额外时机，name==phaseMove 或 技能名 时用
    # DEBUG
        self.skill: str | None = self.parent.skill if self.parent else None     # 发动的技能，继承
        self._phaseMoveOrder: list[str] = self.parent._phaseMoveOrder if self.parent is not None else []      # 本回合原始移动顺序
        self.times = 0     # 循环次数，名字待定
        # self._trigger: bool = True      # 是否触发
    # 时间
        self.timestamp = time.time()        # 事件时间戳
        self.__ftime = time.strftime("%H时%M分%S秒", time.localtime(self.timestamp))        # 调试用观察事件时间
    # 存储所有初始化值
        self.__arg = self.__dict__
