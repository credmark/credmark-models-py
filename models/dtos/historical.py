from credmark.dto import DTO, DTOField


class HistoricalRunModelInput(DTO):
    model_slug: str
    model_input: dict
    window: str
    interval: str
    exclusive: bool = DTOField(False, description='exclude current block')
