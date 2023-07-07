from enum import Enum
from typing import List

from credmark.cmf.model import ModelContext
from credmark.dto import DTO, DTOField, IterableListGenericDTO, PrivateAttr, cross_examples


class HistoricalUnit(str, Enum):
    TIME = 'time'
    BLOCK = 'block'


class BlockNumberSample(DTO):
    number: int
    timestamp: int
    sampleTimestamp: int


class LedgerBlockSeriesOutput(IterableListGenericDTO[BlockNumberSample]):
    blockNumbers: List[BlockNumberSample] = DTOField(default=[],
                                                     description='List of block samples')
    _iterator: str = PrivateAttr('blockNumbers')


class HistoricalDTO(DTO):
    window: str
    interval: str
    exclusive: bool = DTOField(False, description='exclude current block')
    unit: HistoricalUnit = DTOField(HistoricalUnit.TIME,
                                    description="Unit of window and interval")

    class Config:
        schema_extra = {
            'examples': [{'window': '5 days', 'interval': '1 day'},
                         {'window': '5 days', 'interval': '1 day', 'exclusive': False},
                         {'window': '5 days', 'interval': '1 day', 'exclusive': True}]
        }

    def get_blocks(self):
        context = ModelContext.current_context()

        if self.unit is HistoricalUnit.BLOCK:
            model_slug = 'ledger.block-number-series'
            count = int(int(self.window) / int(self.interval))
            model_input = {
                "endBlockNumber": int(context.block_number),
                "interval": int(self.interval),
                "count": count,
                "exclusive": self.exclusive
            }
        else:
            model_slug = 'ledger.block-time-series'
            window_in_seconds = context.historical.to_seconds(self.window)
            interval_in_seconds = context.historical.to_seconds(self.interval)
            count = int(window_in_seconds / interval_in_seconds)
            model_input = {
                "endTimestamp": context.block_number.sample_timestamp,
                "interval": interval_in_seconds,
                "count": count,
                "exclusive": self.exclusive
            }

        return context.run_model(model_slug,
                                 model_input,
                                 return_type=LedgerBlockSeriesOutput
                                 ).blockNumbers


class HistoricalRunModelInput(HistoricalDTO):
    model_slug: str
    model_input: dict

    class Config:
        schema_extra = {
            'examples':  cross_examples(
                [{"model_slug": "aave-v2.token-asset",
                    "model_input": {"symbol": "USDC"}}, ],
                HistoricalDTO.Config.schema_extra['examples'],
                limit=10)
        }
