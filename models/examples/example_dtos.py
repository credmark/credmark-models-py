from credmark.dto import DTO

import logging

class ExampleModelOutput(DTO):
    github_url:str
    documentation_url:str
    message:str = ""

    def __init__(self, **data) -> None:
        super().__init__(**data)

    def log(self, message):
        logger = logging.getLogger('credmark.cmf.model.example')
        logger.info(message)
        self.message += '\n' + message
