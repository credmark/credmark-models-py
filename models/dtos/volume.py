from typing import List
from credmark.cmf.types import Token, Contract
from credmark.dto import DTO, IterableListGenericDTO, DTOField


class TokenTradingVolume(DTO):
    token: Token
    sellAmount: float
    buyAmount: float

    @classmethod
    def default(cls, token):
        return cls(token=token, sellAmount=0, buyAmount=0)


class TradingVolume(IterableListGenericDTO[TokenTradingVolume]):
    tokenVolumes: List[TokenTradingVolume]
    _iterator: str = "tokenVolumes"


class VolumeInput(Contract):
    block_offset: int = DTOField(le=0, description="Offset to the current block (<=0)")

    def split(self, block_end, chunk_size):
        block_start = block_end + self.block_offset + 1
        len_list = block_end - block_start + 1
        for i in range(0, len_list, chunk_size):
            yield block_start + i, min(block_end, block_start + i + chunk_size-1)
