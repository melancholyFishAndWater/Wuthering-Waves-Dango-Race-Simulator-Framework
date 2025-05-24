import logging, random, warnings, sys, time, copy
from typing import Callable, Any, TypeVar
from enum import Enum

"""     日志相关
DEBUG: 测试用，如进入什么时机
INFO: 正常游戏能见到的数据，如前进多少格
ERROR: 错误级日志
"""

logging.basicConfig(
    # filename = "test.log",
    # level = logging.DEBUG
    # level = logging.INFO
    level = logging.ERROR
    )
logger = logging.getLogger(__name__)

# 注释T
T = TypeVar('T')

sys.setrecursionlimit(100)