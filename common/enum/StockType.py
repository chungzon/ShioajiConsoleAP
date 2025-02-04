from enum import Enum

class StockType(Enum):
    DAY_TRADING = 0 # 當沖
    LONG_TERM = 1 # 留倉
    MARGIN_TRADING = 2 # 融資
    SHORT_TRADING = 3 # 融券