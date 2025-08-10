
from typing import TYPE_CHECKING, Self
if TYPE_CHECKING:
    from character import Character
    from gameEvent import GameEvent
    from skill import Skill

class status():
    """仅用于动态存储全局状态，用于连接所有模块，没有任何函数
    """
    _instance = None
    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.player: Character | None = None      # 当前角色
            cls.event: GameEvent       # 当前处理的事件
            cls.players: list[str] = []     # 角色列表
            cls.players_info: dict[str, Character] = {}     # 角色总信息
            cls.skills: list[str] = []      # 技能名列表
            cls.skills_info: dict[str, Skill] = {}        # 存储所有技能对象
            cls.maxLogNumber = 6       # 最多日志数，如果要多次重开，建议开warning级别且这个调低点
        return cls._instance

_status = status()