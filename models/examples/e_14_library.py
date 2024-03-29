import warnings

import matplotlib
import numpy
import pandas
import pyarrow
import scipy
import xlrd
import xlsxwriter
from credmark.cmf.model import Model

from .dtos import ExampleLibrariesOutput

# TODO: Replace statsmodels library.
# This library is deprecated. Suppressing deprecation warning until
# a replacement is found.
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=DeprecationWarning)
    import statsmodels


@Model.describe(
    slug='example.libraries',
    version='1.2',
    display_name='Example - Libraries',
    description='A list of the math/data science libraries that are '
    'included in the Credmark Framework.',
    developer='Credmark',
    category='example',
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
