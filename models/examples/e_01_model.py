from credmark.cmf.model import Model
from credmark.dto import DTO, DTOField
from models.dtos.example import ExampleModelOutput


class EchoExampleInput(DTO):
    message: str = DTOField('Hello', description='A message')


class EchoExampleOutput(ExampleModelOutput):
    echo: str


@Model.describe(slug='example.model',
                version='1.0',
                display_name='Example (Model)',
                description="A test model to echo the message property sent in input.",
                developer='Credmark',
                input=EchoExampleInput,
                output=EchoExampleOutput)
class EchoModel(Model):
    def run(self, input: EchoExampleInput) -> EchoExampleOutput:
        output = EchoExampleOutput(
            github_url="https://github.com/credmark/credmark-models-py/blob/main/models/examples/e_01_model.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/components.html#model-class",
            echo=input.message
        )

        output.log("This is a basic model")
        output.log("You can supply a message (str) as input with default value of Hello")
        output.log_io(input="input.message", output=input.message)

        output.log("It echoes back the input message")
        return output
