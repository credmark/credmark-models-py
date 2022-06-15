from typing import List
from credmark.cmf.types import Token, Contract
from credmark.dto import DTO, IterableListGenericDTO, DTOField


class TokenTradingVolume(DTO):
    token: Token
    sellAmount: float
    buyAmount: float
    sellValue: float
    buyValue: float

    @classmethod
    def default(cls, token):
        return cls(token=token, sellAmount=0, buyAmount=0, sellValue=0, buyValue=0)


class TradingVolume(IterableListGenericDTO[TokenTradingVolume]):
    tokenVolumes: List[TokenTradingVolume]
    _iterator: str = "tokenVolumes"


class TradingVolumes(IterableListGenericDTO[TradingVolume]):
    tradingVolumes: List[TradingVolume]
    _iterator: str = "tradingVolume"


class VolumeInput(Contract):
    pool_info_model: str
    interval: int = DTOField(7200, gt=0,
                             description="Block interval to sum up volume (>0)")
    count: int = DTOField(1, ge=1, description='Count')

    @staticmethod
    def split_by_chunk(block_interval, block_end, chunk_size):
        block_start = block_end - block_interval + 1
        len_list = block_end - block_start + 1
        for i in range(0, len_list, chunk_size):
            yield block_start + i, min(block_end, block_start + i + chunk_size-1)
