from typing import List
from credmark.cmf.types import Token
from credmark.dto import DTO, IterableListGenericDTO


class TokenTradingVolume(DTO):
    token: Token
    sellAmount: int
    buyAmount: int


class TradingVolume(IterableListGenericDTO[TokenTradingVolume]):
    tokenVolumes: List[TokenTradingVolume]
    _iterator: str = "tokenVolumes"
