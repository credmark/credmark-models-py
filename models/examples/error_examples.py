import credmark.model
from credmark.model import EmptyInput, ModelDataErrorDesc
from credmark.model.errors import ModelDataError


@credmark.model.describe(slug='example.data-error',
                         version='1.0',
                         display_name='Data Error Example',
                         description="A test model to generate a ModelDataError.",
                         input=EmptyInput,
                         errors=ModelDataErrorDesc(
                             code=ModelDataError.Codes.NO_DATA,
                             code_desc='Data does not exist'))
class Model1(credmark.model.Model):
    """
    """

    def run(self, input: dict) -> dict:
        raise ModelDataError('Data does not exist', ModelDataError.Codes.NO_DATA)


@credmark.model.describe(slug='example.data-error-2',
                         version='1.0',
                         display_name='Data Error 2 Example',
                         description="A test model to generate a ModelDataError with 2 codes defined.",
                         input=EmptyInput,
                         errors=ModelDataErrorDesc(
                             codes=[(ModelDataError.Codes.NO_DATA,
                                     'Data does not exist'),
                                    (ModelDataError.Codes.CONFLICT,
                                     'Conflicting values in input')])
                         )
class Model2(credmark.model.Model):
    """
    """

    def run(self, input: dict) -> dict:
        raise ModelDataError('Data does not exist', ModelDataError.Codes.NO_DATA)
