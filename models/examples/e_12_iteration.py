from credmark.cmf.model import Model
from credmark.cmf.types import Token
from models.dtos.example import ExampleIterationOutput


@Model.describe(
    slug='example.iteration',
    version='1.2',
    display_name='Example - Iteration',
    description="An example model to demonstrate iterable DTOs",
    output=ExampleIterationOutput)
class ExampleIteration(Model):
    def run(self, _) -> ExampleIterationOutput:
        tokens = ExampleIterationOutput.Tokens(tokens=[Token(symbol="CMK")])
        output = ExampleIterationOutput(
            title="12. Example - Iteration",
            description="This model demonstrates how to create and use iterable DTOs",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_12_iteration.py",
            tokens=tokens
        )

        output.log("To make a class iterable, you need to inherit "
                   "\"IterableListGenericDTO\" and override \"_iterator\" attribute")

        output.log("To create iterable Tokens:")
        output.log_io(
            input="class Tokens(IterableListGenericDTO[Token]):\n"
            "\ttokens: List[Token] = []\n"
            "\t_iterator: str = PrivateAttr('tokens')",
            output="")

        output.log_io(input="tokens = Tokens(tokens=[Token(symbol=\"CMK\")])", output=tokens)

        output.log("More tokens can be added by using append method")
        tokens.append(Token(symbol="DAI"))
        output.log_io(input="tokens.append(Token(symbol=\"DAI\"))", output=tokens)

        output.log("You can iterate over \"tokens\" as you would any other list")
        token_addresses = [token.address for token in tokens]
        output.log_io(input="[token.address for token in tokens]", output=token_addresses)

        output.log("Use the extend function to merge another list into tokens")

        stable_coins = ExampleIterationOutput.Tokens(tokens=[Token(symbol="USDC")])
        tokens.extend(stable_coins)
        output.log_io(input="stable_coins = Tokens(tokens=[Token(symbol=\"USDC\")])",
                      output="")
        output.log_io(input="tokens.extend(stable_coins)",
                      output=tokens)
        return output
