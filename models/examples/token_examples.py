
import credmark.model
from credmark.types import Token, NativeToken
from credmark.dto import DTO


class ExampleTokenLoadingOutput(DTO):
    loadedFromAddress: Token
    loadedFromSymbol: Token
    loadedNativeToken: NativeToken


@credmark.model.describe(slug='example.token-loading',
                         version='1.0',
                         developer='credmark',
                         output=ExampleTokenLoadingOutput)
class ExampleTokenLoading(credmark.model.Model):
    def run(self, input) -> ExampleTokenLoadingOutput:
        cmk = Token(symbol='CMK')

        _ = cmk.symbol

        return ExampleTokenLoadingOutput(
            loadedFromAddress=Token(symbol='AAVE'),
            loadedFromSymbol=cmk,
            loadedNativeToken=NativeToken(),
        )
