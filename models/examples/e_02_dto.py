from credmark.cmf.model import Model
from credmark.cmf.types import Portfolio
from credmark.dto import DTO, DTOField, EmptyInput
from models.dtos.example import ExampleModelOutput


@Model.describe(slug='example.dto',
                version='1.0',
                display_name='Example - DTO',
                description='An example model to demonstrate DTO type',
                developer='Credmark',
                input=EmptyInput,
                output=ExampleModelOutput)
class ExampleDto(Model):
    def run(self, _) -> ExampleModelOutput:
        output = ExampleModelOutput(
            title="2. Example - DTO",
            description="An example model to demonstrate DTO type",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/models/examples/e_02_dto.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/components.html#data-transfer-object-dto")

        output.log("DTOs are classes with typed properties which will serialize and deserialize to and from JSON.")

        class Token(DTO):
            symbol: str
            decimals: int = 18

        output.log_io(input="""
class Token(DTO):
    symbol: str
    total_supply: int = 1000""",
                      output="")

        token = Token(symbol='CMK')
        output.log_io(input="Token(symbol='CMK')", output=token)
        output.log_io(input="token.dict()", output=token.dict())
        output.log_io(input="token.schema_json()", output=token.schema_json())

        output.log("To declare a field as required, you may declare it using just"
                   " an annotation, or you may use an ellipsis (...) as the value:")
        output.log_io(input="""
class Token(DTO):
    a: int
    b: int = ...
    c: int = DTOField(...)""",
                      output="")

        output.log("You can use default_factory to declare field with dynamic value")
        output.log_io(input="""
class Token(DTO):
    uid: UUID = DTOField(default_factory=uuid4)
    updated: datetime = DTOField(default_factory=datetime.utcnow)""",
                      output="")

        output.log("For custom validation, use the validator decorator.")
        output.log_io(input="""
class Token(DTO):
    symbol: str

    @validator('symbol')
    def symbol_must_not_contain_space(cls, v):
        if ' ' in v:
            raise ValueError('must not contain a space')
        return v""",
                      output="")

        return output


class PortfolioSummary(ExampleModelOutput):
    num_tokens: int = DTOField(..., description='Number of different tokens')


@Model.describe(slug='example.dto-type-test-1',
                version='1.0',
                display_name='DTO Type Test 1',
                developer='Credmark',
                input=Portfolio,
                output=PortfolioSummary)
class TestModel(Model):

    def run(self, input: Portfolio) -> PortfolioSummary:
        output = PortfolioSummary(
            title="2b. DTO Type Test 1",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/models/examples/dto_examples.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/components.html#data-transfer-object-dto",
            num_tokens=len(input.positions)
        )

        output.log("This model returns the correct type PortfolioSummary")
        output.log("as we set as \"output\" in the describe() decorator above.")

        return output


@Model.describe(slug='example.dto-type-test-2',
                version='1.0',
                display_name='DTO Type Test 2',
                developer='Credmark',
                input=Portfolio,
                output=PortfolioSummary)
class TestModel2(Model):
    def run(self, input: Portfolio) -> PortfolioSummary:
        output = PortfolioSummary(
            title="2c. DTO Type Test 2",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/models/examples/dto_examples.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/components.html#data-transfer-object-dto",
            num_tokens=len(input.positions)
        )

        output.log("This model will raise an error because we're not returning")
        output.log("the type PortfolioSummary that we set as \"output\"")
        output.log("in the describe() decorator above.")
        return {'xx': 'ss'}  # type: ignore
