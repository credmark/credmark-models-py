from credmark.cmf.model import Model
from credmark.cmf.types import Portfolio
from credmark.dto import DTO, DTOField, EmptyInput
from models.dtos.example import ExampleModelOutput


@Model.describe(slug='example.dto',
                version='1.0',
                display_name='Test Model',
                description='Framework Test Model',
                developer='Credmark',
                input=EmptyInput,
                output=ExampleModelOutput)
class DtoExampleModel(Model):
    def run(self, _) -> ExampleModelOutput:
        output = ExampleModelOutput(
            github_url="https://github.com/credmark/credmark-models-py/blob/main/models/examples/02_dto_examples.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/components.html#data-transfer-object-dto")

        output.log("DTOs are classes with typed properties which will serialize and deserialize to and from JSON.")

        class Token(DTO):
            symbol: str
            total_supply: int = 1000

        output.log("""
class Token(DTO):
    symbol: str
    total_supply: int = 1000""")

        token = Token(symbol='CMK', total_supply=1000)
        output.log_io(input="Token(symbol='CMK', total_supply = 1000)", output=token)
        output.log_io(input="token.dict()", output=token.dict())
        output.log_io(input="token.schema_json()", output=token.schema_json())

        output.log("To declare a field as required, you may declare it using just"
                   " an annotation, or you may use an ellipsis (...) as the value:")
        output.log("""
class Token(DTO):
    a: int
    b: int = ...
    c: int = DTOField(...)""")

        output.log("You can use default_factory to declare field with dynamic value")
        output.log("""
class Token(DTO):
    uid: UUID = DTOField(default_factory=uuid4)
    updated: datetime = DTOField(default_factory=datetime.utcnow)""")

        output.log("For custom validation, use the validator decorator.")
        output.log("""
class Token(DTO):
    symbol: str

    @validator('symbol')
    def symbol_must_not_contain_space(cls, v):
        if ' ' in v:
            raise ValueError('must not contain a space')
        return v""")

        return output


class PortfolioSummary(ExampleModelOutput):
    num_tokens: int = DTOField(..., description='Number of different tokens')


@Model.describe(slug='example.type-test-1',
                version='1.0',
                display_name='Test Model',
                description='Framework Test Model',
                developer='Credmark',
                input=Portfolio,
                output=PortfolioSummary)
class TestModel(Model):

    def run(self, input: Portfolio) -> PortfolioSummary:
        output = PortfolioSummary(
            github_url="https://github.com/credmark/credmark-models-py/blob/main/models/examples/dto_examples.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/components.html#data-transfer-object-dto",
            num_tokens=len(input.positions)
        )

        output.log("This model returns the correct type PortfolioSummary")
        output.log("as we set as \"output\" in the describe() decorator above.")

        return output


@Model.describe(slug='example.type-test-2',
                version='1.0',
                display_name='Test Model',
                description='Framework Test Model',
                developer='Credmark',
                input=Portfolio,
                output=PortfolioSummary)
class TestModel2(Model):
    def run(self, _) -> PortfolioSummary:
        output = PortfolioSummary(
            github_url="https://github.com/credmark/credmark-models-py/blob/main/models/examples/dto_examples.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/components.html#data-transfer-object-dto",
            num_tokens=len(input.positions)
        )

        output.log("This model will raise an error because we're not returning")
        output.log("the type PortfolioSummary that we set as \"output\"")
        output.log("in the describe() decorator above.")
        return {'xx': 'ss'}  # type: ignore
