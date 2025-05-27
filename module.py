from calendar import day_abbr
from math import log
import re
from globals import *

class EventTrigger(Enum):
    """
    事件时机
    
    分为：
    
    游戏开始 ---> 载入角色
    
    回合开始 ---> 进行角色移动排序 ---> 检测技能
    
    准备移动 ---> 获取角色移动步数 ---> 检测技能
    
    移动中 -----> 堆叠移动
    
    移动结束 ---> 是否到达终点 ---> 是否全部到达终点
    
    游戏结束 ---> 得出结果

    Args:
        Enum (enum): 枚举类
    """
    unstart =       0
    game_start =     0b1
    round_start =    0b1 << 1
    move_before =    0b1 << 2
    move_begin =     0b1 << 3
    move_end =       0b1 << 4
    game_end =       0b1 << 5

class MoveResult(Enum):
    """
    涵盖了所有移动结果的枚举

    Args:
        Enum (enum): 枚举类
    """
    undefine =      0
    can_next_step = 0b1
    not_all_moved = 0b1 << 1
    all_moved =     0b1 << 2
    game_end =      0b1 << 3


class Skill:

# 时机
    def isTrigger(self, trigger: EventTrigger):
        """
        判断是否是技能触发时机

        Args:
            trigger (Trigger): 当前时期

        Returns:
            bool: 是否触发
        """
        return self._trigger.value & trigger.value
    def trigger(self):
        return self._trigger
    def setTrigger(self, trigger: EventTrigger):
        self._trigger = trigger

# 生效条件
    def meetCondition(self, data: "EventData") -> bool:
        """
        判断是否满足生效条件

        Args:
            data (EventData): 本局数据
            
        Returns:
            bool: 是否满足
        """
        logger.debug(f"进行技能判定 {self}")
        condition = self._condition
        match condition:
            case _ if isinstance(condition, bool):
                return condition
            case _ if isinstance(condition, float):
                return random.random() < condition
            case _ if callable(condition):
                return condition(data)
            case _:
                logger.exception("判断生效条件函数错误：")
                return False
    def condition(self):
        """
        获取技能生效条件

        Returns:
            _type_: _description_
        """
        return self._condition
    def setCondition(self, condition : float | Callable[["EventData"], bool] | bool ):
        self._condition = condition
    def conditionToFunc(self) -> Callable[["EventData"], bool]:
        condition = self._condition
        match condition:
            case _ if isinstance(condition, bool):
                return lambda data: True
            case _ if isinstance(condition, float):
                return lambda data: random.random() < condition
            case _ if callable(condition):
                return condition
            case _:
                logger.exception("生效条件转函数错误：")
                raise TypeError("生效条件转函数失败，请检查生效条件变量的类型")

# 技能目标
    def isTarget(self, role: "Role | None") -> bool:
        """
        判断角色是否是技能生效目标

        Args:
            role (Role): 判断角色

        Returns:
            bool: 是否是生效目标
        """
        return self._target is role
    def target(self) -> "Role | None":
        return self._target
    def target2(self) -> "Role":
        tar = self._target
        if isinstance(tar, Role):
            return tar
        else:
            raise TypeError("角色目标为None")
    def setTarget(self, target : "Role"):
        self._target = target

# 技能效果
    def skillEffect(self, data : "EventData") -> None:
        """
        技能生效

        Args:
            data (EventData): 本局数据
        """
        logger.info(f"技能【{self.__name}】发动{"：" + self.__describe if self.__describe != "" else ""}")
        self.__effect_times += 1
        effect = self._effect
        match effect:
            case _ if isinstance(effect, int):
                data.addMoveNum(effect)
            case _ if callable(effect):
                tRole = data.nowRole()
                data.setNowRole(self.target())
                effect(data)
                data.setNowRole(tRole)
            case _ if effect is None:
                return
            case _:
                logger.exception("技能生效错误：")
    def effect(self):
        return self._effect
    def setEffect(self, effect : Callable[["EventData"], None]):
        self._effect = effect
    def effectToFunc(self):
        logger.exception("没写，不要调用")
        raise
    def skillEffectToFunc(self) -> Callable[["EventData"], "Role | None"]:
        effect = self.effect()
        match effect:
            case _ if isinstance(effect, int):
                return lambda data: data.addMoveNum(effect)
            case _ if callable(effect):
                return effect
            case None:
                return lambda data: None
            case _:
                logger.exception("技能效果转函数错误：")
                raise TypeError("技能效果转函数失败，请检查技能效果变量的类型")
    
# 技能使用
    def tryUseSkill(self, trigger: EventTrigger, data : "EventData") -> bool:
        """
        尝试使用技能
        
        综合了上面的四大函数，使用技能只需要无脑调用这个即可

        Args:
            trigger (Trigger): 当前触发时机
            data (Data): 本局数据
            
        Returns:
            bool: 是否发动成功
        """
        # t = [self.isTrigger(trigger), self.isTarget(data.getNowRole()), self.isCondition(data)]    # NOICE 非测试请注释掉，且这个会使满足条件就失效的技能报错
        if self.isTrigger(trigger) and self.isTarget(data.nowRole()) and self.meetCondition(data):
            self.skillEffect(data)
            return True
        return False
    def tryUseSkill2(self, trigger: EventTrigger, data: "EventData") -> bool:
        """
        无视当前处理目标，发动技能
        
        一般用于在回合开始时发动

        Args:
            trigger (EventTrigger): 时机
            data (EventData): 数据

        Returns:
            bool: 是否发动成功
        """
        if self.isTrigger(trigger) and self.meetCondition(data):
            self.skillEffect(data)
            return True
        return False

# 技能所有者
    def setOwner(self, role : "Role"):
        self._owner = role
    def owner(self):
        return self._owner

# 技能名字
    def setName(self, name : str):
        self.__name = name
    def name(self) -> str:
        return self.__name

    def setNameFormat(self, format: str):
        self.__name_format = format
    def nameFormat(self) -> str | None:
        return self.__name_format

# 技能介绍
    def setDescribe(self, value : str):
        """
        设置技能描述

        Args:
            value (str): 描述内容
        """
        self.__describe = value
    def describe(self) -> str:
        return self.__describe

# 其他
    def effectTimes(self) -> int:
        """
        返回技能生效次数

        Returns:
            int: 生效次数
        """
        return self.__effect_times

    def copy(self) -> "Skill":
        return copy.copy(self)
    def deepcopy(self) -> "Skill":
        return copy.deepcopy(self)

    def __str__(self) -> str:
        name_format = self.nameFormat()
        if name_format is None:
            return self.name()
        else:
            return name_format.format(self.name)

    def __init__(self, 
                 trigger: EventTrigger, 
                 condition: float | Callable[["EventData"], bool] | bool,
                 effect: int | Callable[["EventData"], "Role | None"] | None,
                 target: "Role | None" = None,
                 name = "",
                 describe = "") -> None:
        """
        技能
        
        技能包括：
        技能生效时机、技能生效条件、技能生效对象、技能生效效果
        
        其他非强制初始化属性：
        名字、描述、目标、所有者
        
        使用Role.appSkill添加技能时，如果目标和所有者为None，会自动设为自身

        Args:
            trigger (Trigger): 生效时机，用于判断是否生效，Trigger.No为不生效
            condition (float, Callable[[Data], None]): 生效条件。float为生效概率，取值为0~1.0；bool为是否触发；可以填函数以判断。如果不满足则结束判断，否则将变量代入effect
            effect (int | Callable[["EventData"], "Role | None"] | None): 生效效果。int为移动步数，填函数自行更改传入数据，填None为无效果，需要后续自行设置。
                其返回值Role暂时无实际作用，目前是为了方便类型检查
            target (Role): 生效目标，不填则为自身
            name (str): 技能名，不填则为技能id
            describe (str): 技能描述
        """
        if effect is None:
            effect = lambda _:None
        if name == "":
            name = str(id(self))
        self._trigger : EventTrigger = trigger
        self._condition : float | Callable[[EventData], bool] | bool = condition
        self._effect : int | Callable[[EventData], Role | None] | None = effect
        self._target : "Role | None" = target
        self.__name = name
        self.__describe = describe
        self._owner : "Role | None" = None
        self.__name_format: str | None = None
        self.__effect_times: int = 0

class Role:

# 赛道
    def resetCell(self):
        """
        重置角色所在格数
        """
        self.__cell = 0
    def cell(self) -> int:
        """
        获取角色当前所在格数

        Returns:
            int: 格数
        """
        return self.__cell
    def isInEndpoint(self, length: int) -> bool:
        """
        判断角色是否在终点

        Args:
            length (int): 赛道长度

        Returns:
            bool: 是否在终点
        """
        return self.cell() >= length
    
# 技能
    def tryUseSkills(self, trigger : EventTrigger, data : "EventData"):
        """
        尝试使用角色的所有技能

        Args:
            trigger (Trigger): 当前触发时机
            data (Data): 数据
        """
        for skill in self._skills.copy():
            skill.tryUseSkill(trigger, data)
    def tryUseSkills2(self, trigger: EventTrigger, data: "EventData"):
        """
        无视当前处理目标使用技能

        Args:
            trigger (EventTrigger): 时机
            data (EventData): 数据
        """
        for skill in self._skills.copy():
            skill.tryUseSkill2(trigger, data)

    def appSkill(self, skill : Skill) -> "Role":
        """
        添加技能
        
        如果在技能时机再添加技能，不会生效。此和copy遍历有关
        
        所有的添加技能都要调用这个
        
        skill.owner若为None，则添加技能时自动设为自己

        Args:
            skill (Skill): 要添加的技能
        """
        logger.debug(f"{self}添加技能 {skill}")
        if skill.target() is None:
            skill.setTarget(self)
        if skill.owner() is None:
            skill.setOwner(self)
        self._skills.append(skill)
        logger.debug(f"{self}现有技能：{[skill2.name() for skill2 in self.skills()]}")
        return self
    
    def addTempSkill(self, skill: Skill) -> "Role":
        """
        立即为角色添加技能
        
        技能生效后，移除此技能
        
        最终会调用appSkill

        Args:
            skill (Skill): 要临时添加的技能

        Returns:
            Role: 角色
        """
        dc_skill = skill.deepcopy()     # NOICE 请不要去掉这个，然后修改skill的生效效果。如果这样写实际效果就是：生效技能生效，这和python引用赋值有关
        
        def pack():
            def newEffect(data: EventData):
                logger.debug("技能生效条件通过，删除临时技能")
                skill.skillEffect(data)
                self.removeSkill(dc_skill)
            return newEffect
        
        dc_skill.setEffect(pack())
        return self.appSkill(dc_skill)
    
    def addTempSkillOfRound(self, skill: Skill, round_num: int = 1) -> "Role":
        """
        延迟round_num回合添加临时技能，此技能一生效被删除，就通常用于充当于下回合状态
        
        实际上触发判断时机为回合开始，绕过了技能目标是否当前所处理的角色判断的逻辑
        
        剩余回合计数器会调用appSkill
        
        skill会通过addTempSkill添加

        Args:
            skill (Skill): 要添加的技能效果
            round_num (int, optional): 延迟的回合数. Defaults to 1.

        Returns:
            Role: 角色本身
        """

        skill2 = Skill(
            EventTrigger.round_start, 
            True, 
            None, 
            self, 
            "剩余回合计数器", 
            "每回合自减1，计数器达到0后为目标添加一个临时技能"
            )
        
        def pack():
            count = round_num
            def triEffect(data: EventData):
                nonlocal count
                count -= 1
                if count <= 0:
                    logger.debug("剩余回合计数器已满足移除条件，被移除")
                    self.addTempSkill(skill)
                    self.removeSkill(skill2)
                    count = None        # NOICE 是否需要将变量设为None，存疑
            return triEffect

        skill2.setEffect(pack())
        self.appSkill(skill2)
        return self
    def addTempSkillOfRound2(self, add_move_num: int, round_num: int = 1) -> "Role":
        """
        同上，但是更简单
        
        round_num回合后必定额外移动add_move_num格，然后失去此效果
        
        实际调用addTempSkillOfRound添加状态（技能）

        Args:
            add_move_num (int): 额外移动格数
            round_num (int, optional): 延迟的回合数. Defaults to 1.

        Returns:
            Role: 角色
        """
        self.addTempSkillOfRound(
            Skill(
                EventTrigger.round_start,
                True,
                add_move_num,
                None,
                "状态：额外移动",
                f"额外移动{add_move_num}格"
            )
        )
        return self
    
    def removeSkill(self, skill : Skill) -> bool:
        """
        删除技能

        Args:
            skill (Skill): 技能对象
            
        Returns:
            bool: 是否删除技能成功
        """
        logger.debug(f"删除技能{skill}")
        self._skills.remove(skill)
        logger.debug(f"剩余技能：{[skill2.name() for skill2 in self.skills()]}")
        return True
    def removeSkill2(self, Id : int) -> bool:
        """
        通过技能id删除技能

        Args:
            Id (int): 技能id
        """
        for skill in self._skills:
            if Id == id(skill):
                self.removeSkill(skill)
                return True
        else:
            logger.error("删除技能失败")
            return False
    
    def skills(self) -> list[Skill]:
        """
        获取技能组

        Returns:
            list[Skill]: 技能组
        """
        return self._skills
    
# 位置
    def setCellNum(self, num : int):
        self.__cell = num
    def addCellNum(self, num : int):
        self.__cell += num

    def generatedMoveNum(self):
        """
        生成移动格数，默认为1,2,3中选一个

        Returns:
            int: 移动格数，默认为1,2,3
        """
        logger.debug("获取移动格数")
        return self._getMoveNum()
    def setMoveFunc(self, func : Callable[[], int]):
        logger.debug("设置获取移动格数的函数")
        self._getMoveNum = func
        return self

# 移动
    def tryHeadRoleMove(self, num : int):
        """
        头上角色也尝试移动

        Args:
            num (int): 移动步数
        """
        result = self.findAllHeadRole()
        for role in result:
            role.move2(num)
    def move(self, num : int, roles: list["Role"]):
        """
        移动，会连带移动头顶的角色，会删除原本底部角色然后设置新底部角色

        Args:
            num (int): 移动数量
            roles (list[Role]): 剩余角色列表
        """
        logger.info(f"{self._name}移动{num}格")
        self.__cell += num
        self.findAndSetBottomRole(roles)
        self.tryHeadRoleMove(num)
    def move2(self, num : int):
        """
        特殊移动。只移动自己，不会删除底部的角色，不会移动头上角色

        Args:
            num (int): 移动数量
        """
        logger.debug(f"{self._name}特殊移动{num}格")
        self.__cell += num

# 堆叠
# 的判断
    def inSameCell(self, role : "Role"):
        """
        判断自己与另一名角色是否处于同一格
        
        不会排除自己

        Args:
            role (Role): 角色

        Returns:
            bool: 是否处于同一格
        """
        return self.__cell == role.__cell
    def isUnStack(self) -> bool:
        """
        返回自己是否不在堆叠状态

        Returns:
            bool: 是否不在堆叠状态
        """
        return (self.headRole() is None) and (self.bottomRole() is None)
    def isStack(self) -> bool:
        """
        返回自己是否在堆叠状态

        Returns:
            bool: 是否在堆叠状态
        """
        return (self.headRole() is not None) or (self.bottomRole() is not None)

# 的查找
    def findAllHeadRole(self) -> list["Role"]:
        """
        找到角色头顶的所有角色，不包括自己

        Returns:
            list[Role]: 角色列表
        """
        l : list[Role] = []
        role = self
        while(role._head is not None):
            role = role._head
            l.append(role)
        return l
    def findAllHeadRoleOfName(self) -> list[str]:
        """
        输出在角色头顶的角色名字列表

        Returns:
            list[str]: 名字列表
        """
        l: list[str] = []
        role = self
        while(role._head is not None):
            role = role._head
            l.append(role.name())
        return l

    def findTopRole(self) -> "Role | None":
        """
        找到角色最顶端的角色

        Returns:
            Role | None: 最顶端的角色
        """
        l = self.findAllHeadRole()
        if l == []:
            return None
        else:
            return l[-1]

# 的修改
    def setStack(self, role : "Role"):
        """
        将自己叠在role上面

        Args:
            role (Role): 底下的角色
        """
        self.setBottomRole(role)

    def headRole(self) -> "Role | None":
        """
        获取头上的角色

        Returns:
            Role | None: 头上的角色
        """
        return self._head
    def setHeadRole(self, role : "Role"):
        """
        设置自己头顶角色
        
        不会排除自己

        Args:
            role (Role): 角色
        """
        self.removeHeadRole()       # TODO 可优化
        logger.debug(f"{self}设置头顶角色为{role}")
        self._head = role
        logger.debug(f"{role}设置底部角色为{self}")
        role._bottom = self
    def removeHeadRole(self):
        """
        尝试删除角色上面的角色
        """
        if self._head is not None:
            logger.debug(f"{self._head}移除底部角色{self._head._bottom}")
            self._head._bottom = None
            logger.debug(f"{self}移除头顶角色{self._head}")
            self._head = None

    
    def bottomRole(self) -> "Role | None":
        return self._bottom
    def setBottomRole(self, role : "Role"):
        """
        设置自己底部角色
        
        不会排除自己

        Args:
            role (Role): 角色
        """
        self.removeBottomRole()     # TODO 可以优化
        logger.debug(f"{self}设置底部角色为{role}")
        self._bottom = role
        logger.debug(f"{role}设置头顶角色为{self}")
        role._head = self
    def removeBottomRole(self):
        """
        删除角色下面的角色
        """
        if self._bottom is not None:
            logger.debug(f"{self._bottom}移除头顶角色{self._bottom._head}")
            self._bottom._head = None
            logger.debug(f"{self}移除底部角色{self._bottom}")
            self._bottom = None
    def findAndSetBottomRole(self, roles: list["Role"]):
        """
        从角色列表中找到第一个和自己在同一格的其他角色，
        然后将此角色设置为自身的底部角色
        
        如果没找到，则尝试删除自身底部角色

        Args:
            roles (list[Role]): 角色列表
        """
        same_cell_role = None
        for role in roles:
            if (role is not self) and (self.inSameCell(role)):
                same_cell_role = role
                break
        
        if same_cell_role is None:
            self.removeBottomRole()
        else:
            self.setBottomRole(same_cell_role)
    
# 角色名
    def name(self):
        """
        返回角色名字

        Returns:
            str: 角色名
        """
        return self._name
    def setName(self, name: str):
        self._name = name
    
    def __str__(self) -> str:
        return self.name()
    
    def __init__(self, name : str) -> None:
        """
        角色

        Args:
            name (str): 角色名字
        """
        self._name = name
        
        self._skills : list[Skill] = []
        self._getMoveNum : Callable[[], int] = lambda : random.choice([1, 2, 3])
        self.__cell = 0    
        self._head : "Role | None" = None
        self._bottom : "Role | None" = None

class RoleData:
    
    def roles(self) -> list[Role]:
        """
        返回角色列表

        Returns:
            list[Role]: 角色列表
        """
        return self._roles
    def addRole(self, role: Role) -> Role:
        """
        添加一名角色

        Args:
            role (Role): 角色
        """
        self._roles.append(role)
        return role
    def removeRole(self, role: Role):
        """
        删除一名角色

        Args:
            role (Role): 角色
        """
        self._roles.remove(role)
    def setRoles(self, roles: list[Role]):
        """
        设置剩余角色列表

        Args:
            roles (list[Role]): 新的剩余角色列表
        """
        self._roles = roles
        
    def __init__(self) -> None:
        self._roles: list[Role] = []

class EventData(RoleData):
    """
    事件数据，包含对局情况和角色相关
    """
    
# 当前处理角色      # TODO 等待移出
    def resetNowRole(self):
        """
        将当前处理角色重置为None
        """
        self.__nowRole = None
    def setNowRole(self, role : Role | None):
        """
        设置当前处理角色

        Args:
            role (Role): 当前处理角色
        """
        logger.debug(f"设置当前处理角色为{role}")
        self.__nowRole = role
    def nowRole(self) -> Role | None:
        """
        获取当前处理的角色
        
        一般用于在技能中获取正在处理角色
        
        技能生效时，会在发动前中临时将处理角色设置为技能目标，在发动结束后会设会原本正在处理角色。
        因此在技能生效中使用，获取的是技能目标。使用owner可获取技能所有者

        Returns:
            Role | None: 当前角色
        """
        return self.__nowRole
    def isNowRole(self, role : Role):
        """
        是当前处理的角色

        Args:
            role (Role): 判断角色

        Returns:
            bool: 是否是当前角色
        """
        return role is self.nowRole()
    def nowRole2(self) -> Role:
        """
        专门将当前处理角色限制在必为角色对象的函数

        Raises:
            TypeError: role类型错误

        Returns:
            Role: 角色
        """
        role = self.nowRole()
        if isinstance(role, Role):
            return role
        else:
            raise TypeError("role类型错误，请检查类型")

# 对局情况
    def isEnd(self) -> bool:
        """
        判断游戏是否结束

        Returns:
            bool: 是否结束
        """
        return len(self._roles) <= 0
    def now(self) -> EventTrigger:
        """
        获取当前事件的时机

        Returns:
            EventEnum: 事件时机
        """
        return self.__now
    def setNow(self, trigger: EventTrigger):
        """
        设置当前事件时点

        Args:
            tri (EventEnum): 时间时机
        """
        logger.debug(f"--{trigger.name}--")
        self.__now = trigger
    def addRound(self):
        """
        回合数加一
        """
        self.__round += 1
    def round(self) -> int:
        """
        获取当前回合数

        Returns:
            int: 回合数
        """
        return self.__round
    def resetRound(self):
        """
        将回合数归零
        """
        self.__round = 0

# 排名
    def setRoleInEndpoint(self, role: Role):
        """
        设置角色进入终点，包括头顶的角色

        Args:
            role (Role): 进入终点的角色
        """
        roles = [role] + role.findAllHeadRole()
        
        rankingNum = len(self.__rankingOfRoles) + 1
        for role in roles:
            logger.info(f"{role._name}进入终点")
            self.removeRole(role)
            self.__rankingOfRoles[role] = rankingNum
    def rankingOfRoles(self):
        return self.__rankingOfRoles

# 移动
    def setMoveOrder(self, moveOrder : list[Role]):
        """
        设置移动顺序

        Args:
            moveOrder (list[Role]): 移动顺序
        """
        self.__moveOrder = moveOrder
    def moveOrder(self) -> list[Role]:
        """
        返回移动顺序

        Returns:
            list[Role]: 移动顺序
        """
        return self.__moveOrder
    def nextMoveRole(self, length: int) -> Role | None:
        """
        返回下一个移动角色

        Returns:
            Role | None: 下一个移动角色，或为无目标、所有角色都移动过
        """
        # role = self.moveOrder()[len(self.movedRoles())]
        for role in (self.moveOrder()[len(self.movedRoles()):]):
            if not role.isInEndpoint(length):
                return role
        else:
            return
    def newMoveOrder(self):
        """
        快速生成一个随机移动顺序，存于自身
        """
        roles = self.roles()
        self.setMoveOrder(
            random.sample(roles, len(roles))
            )

# 移动过
    def movedRoles(self) -> list[Role]:
        """
        返回移动过的角色

        Returns:
            list[Role]: 移动过的角色
        """
        return self.__movedRoles
    def isMoved(self, role: Role) -> bool:
        """
        角色是否已经移动过

        Args:
            role (Role): 判断角色

        Returns:
            bool: 是否移动过
        """
        return role in self.__movedRoles
    def addMovedRole(self, role: Role):
        """
        将一名角色设置为移动过

        Args:
            role (Role): 要设置的角色
        """
        logger.debug(f"设置角色{role.name()}已经移动过")
        self.__movedRoles.append(role)
    def clearMovedList(self):
        """
        清空移动过角色的列表
        """
        logger.debug("清空移动过的角色列表")
        self.__movedRoles.clear()
    def isAllMoved(self) -> bool:
        """
        返回角色是否全部移动过

        Returns:
            bool: 是否全部移动过
        """
        return len(self.moveOrder()) == len(self.movedRoles())

# 移动步数
    def setMoveNum(self, num : int):
        """
        设置移动步数
        
        增加请用addMoveNum

        Args:
            num (int): 移动的步数
        """
        self.__moveNum = num
    def addMoveNum(self, num : int):
        """
        增加移动步数

        Args:
            num (int): 要增加的移动的步数
        """
        self.__moveNum += num
    def moveNum(self) -> int:
        """
        获取移动步数

        Returns:
            int: 移动步数
        """
        return self.__moveNum

# 赛道
    def length(self) -> int:
        """
        获取赛道长度

        Returns:
            int: 长度
        """
        length = self.__length
        if length is None:
            raise TypeError(f"length不应该为None")
        else:
            return length 
    def setLength(self, length: int):
        """
        设置赛道长度

        Args:
            length (int): 长度
        """
        self.__length = length

# 调试
    def setMoveOrderOfSeq(self, role1_seq: int, role2_seq: int):
        """
        将 role1_seq和role2_seq 的移动顺序交换

        Args:
            role1_seq (int): 角色1的序号
            role2_seq (int): 角色2的序号
        """
        move_order = self.moveOrder()
        role1 = move_order[role1_seq]
        move_order[role1_seq] = move_order[role2_seq]
        move_order[role2_seq] = role1
        self.setMoveOrder(move_order)
        return move_order
    def getAllLinkState(self) -> list[str]:
        """
        返回场上所有角色链接状态

        Returns:
            list[str]: 链接状态列表
        """
        result = []
        for role in self.roles():
            l = [role.name()] + role.findAllHeadRoleOfName()
            result.append(" --> ".join(l))
        return result

    def copy(self) -> "EventData":
        return copy.copy(self)
    def deepcopy(self) -> "EventData":
        return copy.deepcopy(self)

# 结果
    def resultToNameDict(self) -> dict[str, int]:
        """
        将run的运行结果转为角色名: 排名

        Returns:
            dict[str, int]: 字典，key为角色名，int为排名
        """
        result = self.rankingOfRoles()
        return {role.name(): num for role, num in result.items()}

    def __init__(self):
        """
        本局数据
        """
        super().__init__()
        self.__moveOrder: list[Role] = []       # 移动顺序
        self.__movedRoles: list[Role] = []      # 移动过的角色
        self.__moveNum: int = 0                 # 移动格数
        self.__nowRole: Role | None = None      # 当前处理角色
        self.__length: int | None = None        # 赛道长度
        self.__rankingOfRoles: dict[Role, int] = {}
        self.__now = EventTrigger.unstart       #当前时机
        self.__round = 0

class EventProcessor:
    """
    游戏事件处理器
    """

# 数据
    def setInitData(self, data: EventData):
        self.__init_data = data
        if data is not None:
            self.__data.setLength(data.length())
    def initData(self) -> EventData | None:
        """
        获取初始化数据

        Returns:
            EventData: 用于初始化的原始数据
        """
        return self.__init_data
    def initData2(self) -> EventData:
        """
        获取严格的初始化数据

        Returns:
            EventData: 用于初始化的原始数据
        """
        init_data = self.__init_data
        if isinstance(init_data, EventData):
            return init_data
        else:
            raise TypeError("初始化数据错误")

    def data(self) -> EventData:
        """
        获取本局游戏数据

        Returns:
            EventData: 本局游戏数据
        """
        return self.__data

    def addRole(self, role: Role) -> Role:
        """
        添加一名新角色到初始数据中

        Returns:
            Role: 角色
        """
        self.initData2().addRole(role)
        return role
    
    def gameStartInit(self):
        """
        初始化游戏开始数据
        """
        logger.debug("进行数据初始化")
        init_data = self.initData2()
        self.__data = init_data.deepcopy()

# 结果
    def resultsToProbability(self, result: dict[str, dict[int, int]], times: int) -> dict[str, dict[int, str]]:
        """
        将角色排名次数转换成百分比

        Args:
            result (dict[str, dict[int, int]]): runs结果
            times (int): runs次数

        Returns:
            dict[str, dict[int, str]]: 角色对应排名概率
        """
        final_return: dict[str, dict[int, str]] = {}
        
        for name in result:
            final_return.setdefault(name, {})
            for ranking_num in result[name]:
                final_return[name][ranking_num] = "{:.2%}".format(result[name][ranking_num] / times)
        
        return final_return
                
# 检测技能
    def checkTrigger(self):
        """
        尝试使用所有角色的技能
        
        每次时机都会检测所有角色的技能，因此相对效率会慢点
        """
        data = self.data()
        roles = data.roles()
        
        for role in roles:
            role.tryUseSkills(data.now(), data)
    def checkTrigger2(self):
        """
        同checkTrigger，但是这是专门在turnStart时，也就是没有当前处理角色时使用的函数
        
        此函数不会检查当前处理角色是否为空

        Args:
            trigger (EventTrigger): 时机
        """
        data = self.data()
        roles = data.roles()
        
        for role in roles:
            role.tryUseSkills2(data.now(), data)

# 主逻辑
    def gameStart(self) -> EventData:
        """
        进行游戏开始时的操作，包括复制初始数据操作

        Returns:
            EventData: 事件数据
        """
        data = self.data()
        logger.info("游戏开始")
        logger.debug("初始化数据")
        self.gameStartInit()
        data.setNow(EventTrigger.game_start)
        return data
    def turnStart(self) -> EventData:
        """
        开启一个新的回合，增加回合数，并生成一个新移动顺序，检测所有角色的触发器

        Returns:
            EventData: 事件数据
        """
        data = self.data()
        data.setNow(EventTrigger.round_start)
        data.clearMovedList()
        data.addRound()
        logger.info(f"第{data.round()}回合")
        data.newMoveOrder()
        logger.debug(f"原始移动顺序为{[role.name() for role in data.moveOrder()]}")
        self.checkTrigger2()
        return data
    def moveBefore(self) -> MoveResult:
        """
        准备阶段

        Returns:
            MoveResult: 只会有两个返回值，all_moved和can_next_step
        """
        self.data().setNow(EventTrigger.move_before)
        data = self.data()
        role = data.nextMoveRole(data.length())
        if role is None:
            return MoveResult.all_moved
        else:
            data.setNowRole(role)
            data.setMoveNum(role.generatedMoveNum())
            logger.debug(f"{role.name()}准备移动{data.moveNum()}格")
            self.checkTrigger()
            return MoveResult.can_next_step
    def moveBegin(self) -> MoveResult:
        self.data().setNow(EventTrigger.move_begin)
        data = self.data()
        role = data.nowRole2()
        role.move(data.moveNum(), data.roles())
        return MoveResult.can_next_step
    def moveEnd(self) -> MoveResult:

        data = self.data()
        data.setNow(EventTrigger.move_end)
        role = data.nowRole2()
        data.addMovedRole(role)
        logger.debug(f"{role}到达{role.cell()}格")
        
        if role.isInEndpoint(data.length()):
            data.setRoleInEndpoint(role)
            self.data().resetNowRole()
            if data.isEnd():
                return MoveResult.game_end
        if data.isAllMoved():
            return MoveResult.all_moved
        else:
            return MoveResult.not_all_moved
    def move(self) -> tuple[EventData, MoveResult]:
        """
        移动一个角色

        Returns:
            tuple[EventData, MoveEndResult]: 
                参数1为事件数据。
                参数2为移动结果，有三种返回值，not_all_moved、all_moved和game_end
        """
        match self.moveBefore():
            case MoveResult.all_moved:
                move_result = MoveResult.all_moved
            case MoveResult.can_next_step:
                self.moveBegin()
                move_result = self.moveEnd()
            case _:
                logger.exception("未定义的结果")
                raise ValueError("函数返回结果错误，请查看情况")
        return self.data(), move_result
    def gameEnd(self) -> EventData:
        """
        结束游戏

        Returns:
            EventData: 事件数据
        """
        data = self.data()
        data.setNow(EventTrigger.game_end)
        data.resetNowRole()
        return data

# 运行      # TODO 返回值有待改进
    def run(self) -> EventData:
        """
        模拟运行

        Returns:
            EventData: 事件数据
        """
        self.gameStart()
        
        while(True):
            self.turnStart()
            while(True):
                move_result = self.move()[1]
                match(move_result):
                    case MoveResult.not_all_moved:
                        continue
                    case MoveResult.all_moved:
                        break
                    case MoveResult.game_end:
                        self.gameEnd()
                        return self.data()
                        # return self.data().rankingOfRoles()
    def runs(self, times: int) -> dict[str, dict[int, int]]:
        """
        多次模拟运行

        Args:
            times (int): 运行次数

        Returns:
            dict[str, dict[int, int]]: 运行结果
        """
        startTime = time.time()
        final_return: dict[str, dict[int, int]] = {}
        for i in range(times):
            new_result_dict = self.run().resultToNameDict()
            
            for name in new_result_dict:
                final_return.setdefault(name, {})
                ranking_num = new_result_dict[name]
                
                final_return[name][ranking_num] = final_return[name].get(ranking_num, 0) + 1

        endTime = time.time()
        # logger.info(f"模拟次数：{times}\n模拟时间：{endTime - startTime}秒")
        print(f"模拟次数：{times}\n模拟时间：{endTime - startTime}秒")
        return final_return

# 示例
    def addExampleTestRole1(self):
        role = self.addRole(Role("测试角色A")).setMoveFunc(lambda: 0)
        
        skill2 = Skill(
            EventTrigger.move_before,
            True,
            2,
            None,
            "状态：额外移动2格"
        )
        
        skill1 = Skill(
            EventTrigger.move_before,
            True,
            lambda data: role.addTempSkillOfRound(skill2),
            None,
            "测试技能A",
            "移动前，下回合必定额外移动2格"
            )
        
        role.appSkill(skill1)

    def addPhoebe(self):
        self.addRole(Role("菲比")).appSkill(
            Skill(
                EventTrigger.move_before,
                0.5,
                1,
                None,
                "菲比的技能",
                "50%概率额外移动1格"
            )
        )
    
    def addZaNi(self):
        role = self.addRole(Role("赞妮"))
        role.setMoveFunc(lambda: random.choice([1, 3]))
        role.appSkill(
            Skill(
                EventTrigger.move_before,
                lambda data: role.isStack() and random.random() < 0.4,
                lambda data: role.addTempSkillOfRound2(2),
                None,
                "赞妮的技能",
                ""
            )
        )
    
    def addBrant(self):
        # 由于是进行深拷贝再模拟，因此不要直接写is role
        role = self.addRole(Role("布兰特"))
        role.appSkill(
            Skill(
                EventTrigger.move_before,
                lambda data: data.moveOrder()[0] is data.nowRole2(),
                2,
                None,
                "布兰特的技能",
                "如果是第一个移动，额外移动2格"
            )
        )
    
    def addRoccia(self):
        role = self.addRole(Role("洛可可"))
        role.appSkill(
            Skill(
                EventTrigger.move_before,
                lambda data: data.moveOrder()[-1] is data.nowRole2(),
                2,
                None,
                "洛可可的技能",
                "如果是最后一个移动，额外移动2格"
            )
        )

    def exampleOutput(self, result: dict[str, dict[int, str]]):
        """
        在终端以表格输出结果

        Args:
            result (dict[str, dict[int, str]]): runs结果
        """
        from prettytable import PrettyTable

        data_long = len(result.values())
        data_wide = len(result)
        
        arr = [
            ["角色&排名"] + [f"第{i+1}名" for i in range(data_long)],
        ]
        
        for name in result:
            tArr = [name]
            for i in range(data_long):
                probability = result[name].get(i+1, "0%")
                tArr.append(probability)
            arr.append(tArr)
        
        table = PrettyTable()
        table.field_names = arr.pop(0)
        table.add_rows(arr)
        print(table)


    def __init__(self, length: int) -> None:
        """
        事件类
        
        常用函数有：
            run: 进行一次运行
            runs: 进行多次运行

        Args:
            length (int): 赛道长度
        """
        # self.__now: EventTrigger = EventTrigger.unStart
        self.__init_data: EventData = EventData()
        self.__init_data.setLength(length)
        self.__data: EventData = EventData()
        # self.gameStartInit()
        # self.__round = 0
