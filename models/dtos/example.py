import logging
from typing import Union

from credmark.cmf.model.errors import ModelBaseError
from credmark.dto import DTO


class ExampleModelOutput(DTO):
    github_url: str
    documentation_url: str
    message: str = ""

    def log(self, message: str):
        logger = logging.getLogger('credmark.cmf.model.example')
        logger.info(message)
        self.message += '\n' + message

    def log_io(self, input: str, output):
        self.log(f"{input} : {output}")

    def log_error(self, error: Union[str, Exception]):
        if isinstance(error, str):
            self.log(error)
        elif isinstance(error, ModelBaseError):
            self.log(error.data.message)
        else:
            self.log(str(error))
