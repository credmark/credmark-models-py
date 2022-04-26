from credmark.cmf.model import Model
from models.dtos.example import ExampleEchoInput, ExampleEchoOutput


@Model.describe(
    slug='example.model',
    version='1.2',
    display_name='Example - Model',
    description="First example model to echo the message property sent in input.",
    developer='Credmark',
    input=ExampleEchoInput,
    output=ExampleEchoOutput)
class ExampleEcho(Model):
    def run(self, input: ExampleEchoInput) -> ExampleEchoOutput:
        output = ExampleEchoOutput(
            title="1. Example - Model",
            description="First example model to echo the message property sent in input.",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_01_model.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "components.html#model-class",
            echo=f"{input.message} from block: {self.context.block_number}"
        )

        output.log("This is a basic model")
        output.log("You can supply a message (str) as input with default value of Hello")
        output.log_io(input="input.message", output=input.message)

        output.log("It echoes back the input message with execution context's block number "
                   "and its timestamp")
        return output
