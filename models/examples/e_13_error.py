from credmark.cmf.model import Model, EmptyInput, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError


@Model.describe(
    slug='example.data-error-1',
    version='1.2',
    display_name='Example - Data Error 1',
    description="An example model to generate a ModelDataError.",
    developer='Credmark',
    input=EmptyInput,
    errors=ModelDataErrorDesc(code=ModelDataError.Codes.NO_DATA,
                              code_desc='Data does not exist'))
class ExampleDataError1(Model):
    def run(self, _) -> dict:
        raise ModelDataError('Data does not exist', ModelDataError.Codes.NO_DATA)


@Model.describe(
    slug='example.data-error-2',
    version='1.2',
    display_name='Example - Data Error 2',
    description="An example model to generate a ModelDataError with 2 codes defined.",
    developer='Credmark',
    input=EmptyInput,
    errors=ModelDataErrorDesc(
        codes=[(ModelDataError.Codes.NO_DATA, 'Data does not exist'),
               (ModelDataError.Codes.CONFLICT, 'Conflicting values in input')])
)
class ExampleDataError2(Model):
    def run(self, _) -> dict:
        raise ModelDataError('Conflicting values in input', ModelDataError.Codes.CONFLICT)
