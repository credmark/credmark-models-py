import bs4
import matplotlib
import numpy
import pandas
import pyarrow
import scipy
import statsmodels
import xlrd
import xlsxwriter
from bs4 import BeautifulSoup
from credmark.cmf.model import Model
from credmark.dto import EmptyInput
from models.dtos.example import ExampleLibrariesOutput


@Model.describe(
    slug='example.libraries',
    version='1.2',
    display_name='Example - Libraries',
    description='A list of the math/data science libraries that are '
    'included in the Credmark Framework.',
    developer='Credmark',
    input=EmptyInput,
    output=ExampleLibrariesOutput)
class ExampleLibraries(Model):
    def run(self, _) -> ExampleLibrariesOutput:
        libraries = [
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

        output = ExampleLibrariesOutput(
            title="14. Example - Libraries",
            description="This model lists the math/data science libraries that are "
            "included in the Credmark Framework.",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_14_library.py",
            libraries=libraries
        )

        output.log_io(input="", output=output.libraries)

        return output
