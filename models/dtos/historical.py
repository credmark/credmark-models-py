from credmark.dto import DTO, DTOField, cross_examples


class HistoricalDTO(DTO):
    window: str
    interval: str
    exclusive: bool = DTOField(False, description='exclude current block')

    class Config:
        schema_extra = {
            'examples': [{'window': '5 days', 'interval': '1 day'},
                         {'window': '5 days', 'interval': '1 day', 'exclusive': False},
                         {'window': '5 days', 'interval': '1 day', 'exclusive': True}]
        }


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
