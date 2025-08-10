from __future__ import annotations
import logging
import random
from typing import TYPE_CHECKING, Callable, Self, Optional
if TYPE_CHECKING:
    from skill import Skill
    from logging import Logger
    from type.status import status
    from gameEvent import GameEvent
    from game import GameCompatible

game: GameCompatible
_status: status
logger: Logger
GLOBAL_IMPORT = False

class Character:
    """角色类
    """    
# 技能
    def check(self, event: GameEvent) -> list[str]:
        """
        检测角色是否有技能发动

        Args:
            event (GameEvent): 检测事件

        Returns:
            list[str]: 发动的技能
        """
        result: list[str] = []
        skills = self.skills
        for skill in skills:
            skill_info = _status.skills_info[skill]
            if skill_info.check(event, self):
                result.append(skill)
        return result
    
    def addSkill(self, name: str | Skill) -> Self:
        """
        添加技能

        Args:
            name (str | Skill): 要添加的技能，字符串则默认已注册

        Returns:
            Self: 自身
        """
        logger.debug(f"{self}添加技能 {name}")
        if isinstance(name, str):
            if name in self.skills:
                logger.warning(f"尝试为角色{self}添加一个已有技能：{name}")
            else:
                self.skills.append(name)
        else:
            game.registerSkill(name)
            self.skills.append(name.name)
        logger.debug(f"{self}现有技能：{self.skills}")
        return self
    
    def addTempSkill(self, name: str | Skill) -> Self:      # WARN 未测试
        """
        添加临时技能
        
        临时技能不会log，除非你在debug或低日志级别，或者添加完后手动设置
        
        技能生效后，移除此技能

        Args:
            name (str | Skill): 要临时添加的技能

        Returns:
            Self: 自身
        """
        skill = _status.skills_info[name] if isinstance(name, str) else name
        cSkill = skill.deepcopy()
        # cSkill.name = cSkill.name + "_temp"
        def pack():
            content = skill.content
            newName = cSkill.name
            plt = self
            def con(event: GameEvent, player: Character):
                content(event, player)
                plt.removeSkill(newName)
                game.unregisterSkill(newName)
            return con
        if not (__debug__ or logger.level <= logging.DEBUG):
            cSkill.logSkill = False
        cSkill.content = pack()
        self.addSkill(cSkill)
        return self
    
    def removeSkill(self, skill: str) -> Self:
        """
        删除技能

        Args:
            skill (str): 技能名
            
        Returns:
            Self: 自身
        """
        logger.debug(f"删除技能{skill}")
        self.skills.remove(skill)
        logger.debug(f"剩余技能：{self.skills}")
        return self
        
# 堆叠
    def append(self, player: Character):
        if not self.headPlayer:
            self.headPlayer = player
            player.bottomPlayer = self
            logger.info(f"{player}堆在了{self}头上")
            return
        last_player = self.headPlayer
        while last_player.headPlayer:
            last_player = last_player.headPlayer
        last_player.headPlayer = player
        player.bottomPlayer = last_player
        logger.info(f"{player}堆在了{last_player}头上")
        
    def findAllHeadPlayer(self) -> list[Character]:
        """
        返回所有头顶角色的列表

        Returns:
            list[Character]: 角色列表
        """
        result: list[Character] = []
        current = self.headPlayer
        while current:
            result.append(current)
            current = current.headPlayer
        return result
    
    def findTop(self) -> Character:
        """
        获得角色最顶端的角色，包含该角色

        Returns:
            Character: 最顶端的角色
        """
        plt = self
        while plt.headPlayer:
            plt = plt.headPlayer
        return plt
    
    def deleteBottom(self):

        """
        删除下面的角色
        """
        if self.bottomPlayer:
            self.bottomPlayer.headPlayer = None
            self.bottomPlayer = None

# 移动
    def move(self, num: int):
        """
        基础移动，会连带移动头顶的角色，会删除原本底部角色然后设置新底部角色

        Args:
            num (int): 移动步数
        """
        self.deleteBottom()
        order = self.findAllHeadPlayer()
        logger.info(f"{self}前进了{num}格")
        self.cell += num
        game.movedPlayers.append(self.name)
        for plt in order:
            logger.info(f"{plt}因{self}移动，前进了{num}格")
            plt.cell += num
        order = [self] + order
        inSameCellPlts = [p for p in game.getPlayers() if p not in order and p.cell == self.cell]
        if len(inSameCellPlts) > 0:
            inSameCellPlts[0].findTop().append(self)
        
    def move2(self, num : int):
        """
        特殊移动。只移动自己，不会影响头尾角色的位置，也不会断开链表

        Args:
            num (int): 移动数量
        """
        logger.debug(f"{self.name}特殊移动{num}格")
        self.cell += num
        game.movedPlayers.append(self.name)
    
    def move3(self):        # FEAT 好像会有点吵啊，这个函数
        """
        细化的移动，一步一步移动
        """
        self.move(1)
        
    def __str__(self) -> str:
        return self.name

    def __init__(self, name: str, skills: list[str] = []) -> None:
        """
        角色

        Args:
            name (str): 角色名字
            skills (list[str], optional): 技能列表，必须先往game里注册技能. Defaults to [].
        """
        if not GLOBAL_IMPORT:
            from game import game as g, _status as s, logger as l
            global game, _status, logger
            game, _status, logger = g, s, l
        # args
        self.name = name        # 角色名
        self.skills: list[str] = [] if len(skills)==0 else skills      # 技能组
        self.getMoveNum: Callable[[], int] = lambda: random.choice([1, 2, 3])      # 角色骰子
        self.cell = 0    # 角色所在格
        self.headPlayer: Optional[Character] = None     # 头顶角色
        self.bottomPlayer: Optional[Character] = None       # 底下角色
