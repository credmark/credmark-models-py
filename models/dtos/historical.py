from credmark.dto import DTO, DTOField

class HistoricalDTO(DTO):
    window: str
    interval: str
    exclusive: bool = DTOField(False, description='exclude current block')


class HistoricalRunModelInput(HistoricalDTO):
    model_slug: str
    model_input: dict
