from typing import Any, List
import credmark.model
from credmark.types.dto import DTO
import pandas
import numpy
import matplotlib
import scipy
import statsmodels
import xlrd
import xlsxwriter
import bs4
from bs4 import BeautifulSoup
import pyarrow


class LibrariesDto(DTO):
    libraries: List[Any]


@credmark.model.describe(slug='example.libraries',
                         version='1.0',
                         display_name='Libraries',
                         description=("A list of the math/data science libraries that are "
                                      "included in the Credmark Framework."),
                         output=LibrariesDto)
class ExampleLibraries(credmark.model.Model):
    def run(self, input) -> LibrariesDto:
        return LibrariesDto(
            **{
                "libraries": [
                    {
                        "name": pandas.__name__,
                        "version": pandas.__version__
                    },
                    {
                        "name": numpy.__name__,
                        "version": numpy.__version__
                    },
                    {
                        "name": matplotlib.__name__,
                        "version": matplotlib.__version__,  # type: ignore
                    },
                    {
                        "name": scipy.__name__,
                        "version": scipy.__version__
                    },
                    {
                        "name": statsmodels.__name__,
                        "version": statsmodels.__version__
                    },
                    {
                        "name": xlrd.__name__,
                        "version": xlrd.__version__
                    },
                    {
                        "name": xlsxwriter.__name__,
                        "version": xlsxwriter.__version__
                    },
                    {
                        "name": BeautifulSoup.__name__,
                        "version": bs4.__version__  # type: ignore
                    },
                    {
                        "name": pyarrow.__name__,
                        "version": pyarrow.__version__
                    },
                ]
            }
        )
