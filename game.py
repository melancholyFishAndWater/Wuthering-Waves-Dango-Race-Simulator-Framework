from __future__ import annotations
import random
import time
from typing import Optional, Self
from gameEvent import GameEvent
from character import Character
from skill import Skill
from type.Signal import Signal, SkillTrigger
from type.status import _status

class GameCompatible:
    """
    游戏管理器
    """
    _instance = None
# 调试
    def getOuts(self) -> dict[str, int]:
        """
        返回赛况

        Returns:
            dict[str, int]: 返回角色名: 所在格的字典
        """
        plts = game.getPlayers()
        plts.sort(key=lambda p: p.cell, reverse=True)
        return {item.name: item.cell for index, item in enumerate(plts)}

# 角色与技能    
    def registerSkill(self, skill: Skill) -> Skill:
        """
        注册技能

        Args:
            skill (Skill): 技能
        
        Returns:
            Skill: 注册完的技能
        """
        if skill.name in _status.skills:
            logger.warning(f"尝试注册一个已有技能：{skill}，原有技能将会被覆盖")
        else:
            _status.skills.append(skill.name)
        _status.skills_info[skill.name] = skill
        return skill

    def unregisterSkill(self, skill: str | Skill) -> str | Skill:
        """
        注销技能

        Args:
            skill (str | Skill): 技能

        Returns:
            str | Skill: 被注销的技能
        """
        name = skill if isinstance(skill, str) else skill.name
        if name in _status.skills:
            _status.skills.remove(name)
            del _status.skills_info[name]
        else:
            logger.warning(f"要注销的技能：{skill}不存在")
        return skill
    
    def registerPlayer(self, player: Character | str, skills: list[str | Skill] | str | Skill = []) -> Character:
        """
        注册角色

        Args:
            player (Character | str): 角色
            skills (list[str | Skill] | str | Skill, optional): 角色技能，若为字符串类型，默认已注册，写了这个后可以在创建角色时不添加技能. Defaults to [].

        Returns:
            Character: 注册完的角色
        """
        plt = player if isinstance(player, Character) else Character(player)
        if not isinstance(skills, list):
            skills = [skills]
        for i in skills:
            plt.addSkill(i)
        if plt.name in _status.players:
            logger.warning(f"尝试注册已存在的角色，原有角色将会被覆盖")
        else:
            _status.players.append(plt.name)
        _status.players_info[plt.name] = plt
        return plt
     
    def addSkill(self, name: str, skill: Skill | str) -> Optional[str]:     # FEAT 合法性检测
        """
        给一名角色添加技能

        Args:
            name (str): 角色名
            skill (Skill): 技能
        """
        if isinstance(skill, str):
            result = skill
            plt = _status.players_info[name]
            plt.skills.append(result)
        elif isinstance(skill, Skill):
            result = skill.name
            self.registerSkill(skill)
            plt = _status.players_info[name]
            plt.skills.append(result)
        else:
            return
        logger.debug(f"{plt}获得技能{skill}")
        return result
    
    def addCharacter(self, name: str | Character, skills: list[str | Skill] | str | Skill = []) -> Optional[Character]:
        """
        添加添加一个已注册的角色进入游戏

        Args:
            name (str | Character): 角色名
            skills (list[str | Skill] | str | Skill, optional): 额外技能列表，字符串则视为技能已注册. Defaults to [].
        
        Returns:
            Optional[Character]: 添加成功则返回角色对象，否则返回None
        """        
        if not isinstance(skills, list):
            skills = [skills]
        l = []
        for s in skills:
            if isinstance(s, Skill):
                self.registerSkill(s)
                l.append(s.name)
            else:
                l.append(s)
        plt = None
        if isinstance(name, str):
            if name in _status.players_info.keys():
                plt = _status.players_info[name]
            else:
                logger.warning(f"未找到角色{name}")
        else:
            plt = name
            self.registerPlayer(plt)
        if plt:
            game.players.append(plt.name)
        return plt
    
    def getCells(self) -> list[int]:
        """
        获取所有角色所在格

        Returns:
            list[int]: 所在格列表
        """
        return [_status.players_info[i].cell for i in game.players]
    
    def getPlayers(self) -> list[Character]:
        """
        返回所有角色对象列表

        Returns:
            list[Character]: 对象列表
        """
        return [_status.players_info[i] for i in game.players]

# 导入
    def importStandard(self):
        """
        导入标准角色
        """
        # 今汐 不是，这什么技能描述
        def jinxiSkill(event: GameEvent, player: Character):
            head = player.headPlayer
            top = player.findAllHeadPlayer()[-1]
            assert head
            head.deleteBottom()
            top.append(player)
        game.registerPlayer("今汐",
            Skill(
                # trigger=SkillTrigger(_global="roundEnd"),     # FEAT
                filter=lambda e, p: p.headPlayer is not None and random.random() <= 1,
                content=jinxiSkill,
                name="jinxiSkill",
                info="如果头顶堆叠其他团子，有40%的概率移动到所有团子的最上方"
            )
        )
        
        # 长离
        def changliSkill(e, p: Character):
            temp = Skill(
                trigger=SkillTrigger(_global = "roundBegin"),
                filter=True,
                content= lambda: game.phaseMoveOrder.remove(p.name) and game.phaseMoveOrder.append(p.name),
                info="回合开始后，将自己的移动顺序设置为最后一位",       # NOICE 好像描述得不太对
                name=__name__
            )
            p.addTempSkill(temp)
        game.registerPlayer("长离",
            Skill(
                trigger=SkillTrigger(_global="roundEnd"),
                filter=lambda e, p: p.bottomPlayer is not None and random.random() <= 0.65,
                content=changliSkill,
                info="回合结束时，如果下方堆叠其他团子，下一个回合有65%的概率最后一个行动"
            )
        )
        
        # 卡卡罗 恰恰罗
        def kakaluoFilter(e, p: Character):
            cells = game.getCells()
            cells.remove(p.cell)
            return all(p.cell < i for i in cells)
        game.registerPlayer("卡卡罗",
            Skill(
                trigger=SkillTrigger(player="phaseMoveBegin"),
                filter=kakaluoFilter,
                content=3,
                info="开始移动时，如果在最后一名，额外前进3格"
            )
        )
        
        # 守岸人 岸宝 tested
        game.registerPlayer("守岸人",
            Skill(info="骰子只会掷出2或3")
        ).getMoveNum = lambda: random.choice([2, 3])
        
        # 椿
        def chunSkill(e: GameEvent, p: Character):
            e._finished = True
            if p.headPlayer:
                p.headPlayer.deleteBottom()
            p.deleteBottom()
            cells = game.getCells()
            count = 0
            for i in cells:
                if i == p.cell:
                    count += 1
            p.move2(count)
        game.registerPlayer("椿",
            Skill(
                trigger=SkillTrigger(player="phaseMoveBegin"),
                filter=0.5,
                content=chunSkill,
                info="自身行动时50%概率触发：当前格子除了自身外每有1个团子，使自身行动格数+1，且不会带其他团子一起移动"
            )
        )
        
        # 珂莱塔
        def kelaitaSkill(e: GameEvent, p: Character):
            temp = Skill(
                trigger=SkillTrigger(player="phaseMoveBefore"),
                filter=True,
                content=lambda e: e._finished,
                info="准备移动时，跳过投掷骰子，然后以上一次投掷的投掷数移动",
                name=__name__
            )
            p.removeSkill(__name__)
            p.addTempSkill(temp)
            e.trigger("phaseMove")
            p.addSkill(__name__)
        game.registerPlayer("珂莱塔",
            Skill(
                trigger=SkillTrigger(player="phaseMoveBegin"),
                filter=0.28,
                content=kelaitaSkill,
                info="28%概率以骰子的步数前进2次"
            )
        )
        
        # 洛可可 tested
        game.registerPlayer("洛可可",
            Skill(
                trigger=SkillTrigger(player="phaseMoveBegin"), 
                filter=lambda e: e.player is not None and e.player.name == game.phaseMoveOrder[-1], 
                content=2, 
                info="如果是最后一个移动，额外前进2格")
        )
        
        # 布兰特 tested
        game.registerPlayer("布兰特",
            Skill(
                trigger=SkillTrigger(player="phaseMoveBegin"), 
                filter=lambda e: e.player is not None and e.player.name == e._phaseMoveOrder[0], 
                content=2, 
                info="如果是第一个移动，额外前进2格"
            )
        )
        
        # 坎特蕾拉  # TODO
        
        # 赞妮 同一格有人就行 tested
        def zanniFilter(e, p: Character):
            cells = game.getCells()
            cells.remove(p.cell)
            return any(p.cell == i for i in cells) and random.random() <= 0.4
        zanniSubSkill = Skill(trigger=SkillTrigger(player="phaseMoveBegin"), filter=True, content=2, info="额外前进2格")
        zanniSubSkill.logSkill = True
        znniSkill = Skill(
            trigger=SkillTrigger(player="phaseMoveBegin"),
            filter=zanniFilter,
            content=lambda e, p: p.addTempSkill(zanniSubSkill),
            info="骰子只会掷出1或3。开始移动时，如果处于堆叠状态下回合有40%概率额外前进2格",
            logSkill=False
        )
        znniSkill.logSkill = False
        game.registerPlayer("赞妮", znniSkill).getMoveNum = lambda: random.choice([1, 3])
        
        # 卡提希娅  tested
        def katixiyaFilter(e, p: Character):
            plts = filter(lambda i: i != p, game.getPlayers())
            return all(p.cell < i.cell for i in plts)
        katixiyaSkill_1 =   Skill(
            trigger=SkillTrigger(player="phaseMoveBegin"),
            filter=0.6,
            content=2,
            info="移动时，60%概率额外前进2格"
        )
        katixiyaSkill = Skill(
                trigger=SkillTrigger("phaseMoveEnd"),
                filter=katixiyaFilter,
                content=lambda e, p: p.addSkill(katixiyaSkill_1),
                name="katixiyaSkill",
                info="自身移动结束后，若处于最后一名，本场比赛剩余回合都会60%概率额外前进2格。每场比赛最多触发1次"
        )
        game.registerPlayer("卡提希娅").addTempSkill(katixiyaSkill)
        katixiyaSkill.logSkill = True
        
        # 菲比 菲比啾比 tested
        game.registerPlayer("菲比",
            Skill(trigger=SkillTrigger(
                player="phaseMoveBegin"), 
                filter=0.5, 
                content=1, 
                name="feibiSkill",
                info="50%概率额外前进1格"
            )
        )

# 游戏控制
    def reStart(self, evt: GameEvent):
        """
        快速重开游戏

        Args:
            evt (GameEvent): init的返回值/上局游戏的结果，里面存储了gameInit后的信息
        """
        self.atEndPlayers = []
        self.movedPlayers = []
        self.phaseMoveOrder = []
        self.roundNumber = 0
        
        _status.player = None
        _status.event = evt
        evt._phaseMoveOrder = []
        if not self.NeedAllGameEvents:
            evt.childEvents = []
        evt.start()
            
    def init(self) -> GameEvent:
        """
        初始化游戏

        Returns:
            GameEvent: 初始化完毕的事件
        """
        self.importStandard()
        next = self.createEvent("gameInit", None)
        _status.event = next
        return next
        
    def faseStart(self):    # FEAT
        """
        快速开始一场游戏

        Returns:
            dict[str, int]: 结果
        """
        self.init()
        game.addCharacter("守岸人")
        # game.addCharacter("洛可可")
        # game.addCharacter("布兰特")
        evt = self.start()
        result = evt.getResult()
        if __debug__:
            logger.debug("游戏结束，请自行调试或结束进程")
            breakpoint()
        return result
    
    def start(self, event: Optional[GameEvent] = None) -> GameEvent:
        """
        开始游戏
        
        如果事件不存在，则开始 _status.event

        Args:
            event (Optional[GameEvent], optional): 准备开始的事件. Defaults to None.

        Returns:
            GameEvent: 执行完毕的事件
        """
        if event:
            return event.start()
        else:
            return _status.event.start()
            # raise ValueError("不可loop的event！")
    
    def createEvent(self, name: Signal, triggerEvent: Optional[GameEvent] = None):
        """
        创建事件
        
        triggerEvent为父事件，如果存在，父事件的next为此事件；如果没有则将_status.event设为创建的事件，并将此事件加入事件池

        Args:
            name (str): 事件名
            triggerEvent (Optional[GameEvent]): 父事件。默认None。
            
        Returns:
            GameEvent: 创建的事件
        """
        from gameEvent import GameEvent
        next = GameEvent(name=name)
        if (triggerEvent is not None):
            triggerEvent.next = next
        else: 
            _status.event = next
        return next
    
    def log(self, msg: str):
        """
        快速以info级别输出

        Args:
            message (str): 输出信息
        """
        logger.info(msg)

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.roundNumber = 0        # 轮数
            cls.players: list[str] = []        # 本局参与游戏的角色
            cls.phaseMoveOrder: list[str] = []      # 本轮移动顺序
            cls.movedPlayers: list[str] = []        # 移动过的角色
            cls.atEndPlayers: list[str] = []        # 在终点的角色
            cls.cells = 24     # 赛道长度
            cls.NeedAllGameEvents = __debug__ and True      # 是否需要所有局的信息，用于快速重开时节省内存
        return cls._instance

game = GameCompatible()

"""     日志相关
DEBUG: 测试用，如进入什么时机
INFO: 正常游戏能见到的数据，如前进多少格
ERROR: 错误级日志
"""
import logging
from os.path import join as joinPath
def reNameFile():
    from os import mkdir, rename
    from os.path import exists as existsFile, getmtime
    if not existsFile('log'):
        mkdir('log')
    else:
        file = joinPath('log', 'new.log')
        if existsFile(file):
            name = time.strftime("%d日%H时%M分%S秒.log", time.localtime(getmtime(file)))
            rename(file, joinPath('log', name))
reNameFile()
logging.basicConfig(
    filename = joinPath('log', "new.log"),
    encoding="utf-8"
)
logger = logging.getLogger(__name__)
logger.setLevel(
    # level = logging.DEBUG
    level=logging.INFO
    # level = logging.WARNING
)
def clearLog():
    from os import listdir, remove as removeFile
    l = listdir(joinPath("log"))
    l = [name for name in l if name[-4:] == '.log']
    if len(l) >= _status.maxLogNumber:
        l.sort()
        for file in l[:-_status.maxLogNumber]:
            logger.debug(f"日志超出上限，删除日志：{file}")     # NOICE 没有确认机制，是不是...
            removeFile(joinPath("log", file))
clearLog()
        
