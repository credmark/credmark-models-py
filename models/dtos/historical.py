from credmark.dto import DTO

class HistoricalRunModelInput(DTO):
    model_slug: str
    model_input: dict
    window: str
    interval: str
