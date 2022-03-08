from typing import Any, List
import credmark.model
from credmark.types.dto import DTO
import pandas
import numpy


class LibrariesDto(DTO):
    libraries: List[Any]


@credmark.model.describe(slug='example.libraries',
                         version='1.0',
                         display_name='Libraries',
                         description="A list of the math libraries that are included in the Credmark SDK.",
                         output=LibrariesDto)
class ExampleLibraries(credmark.model.Model):
    def run(self, input) -> LibrariesDto:
        return LibrariesDto(
            **{
                "libraries": [
                    {
                        "name": pandas.__name__,
                        "version": pandas.__version__},
                    {
                        "name": numpy.__name__,
                        "version": numpy.__version__
                    }
                ]
            }
        )
