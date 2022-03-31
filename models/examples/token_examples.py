
from credmark.cmf.model import Model
from credmark.cmf.types import Token, NativeToken
from credmark.dto import DTO


class ExampleTokenLoadingOutput(DTO):
    loadedFromAddress: Token
    loadedFromSymbol: Token
    loadedNativeToken: NativeToken


@Model.describe(slug='example.token-loading',
                version='1.0',
                developer='credmark',
                output=ExampleTokenLoadingOutput)
class ExampleTokenLoading(Model):
    def run(self, input) -> ExampleTokenLoadingOutput:
        cmk = Token(symbol='CMK')

        return ExampleTokenLoadingOutput(
            loadedFromAddress=Token(symbol='AAVE'),
            loadedFromSymbol=cmk,
            loadedNativeToken=NativeToken(),
        )
