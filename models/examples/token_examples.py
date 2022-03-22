
from typing import Union
import credmark.model
from credmark.types import Token, Address
from credmark.dto import DTO


class ExampleTokenLoadingOutput(DTO):
    loadedFromAddress: Token
    loadedFromSymbol: Token
    loadedNativeToken: Token
    loadedFromSymbolPrice: Union[float, None]
    loadedFromSymbolTotalSupply: float
    loadedFromSymbolBalanceOf: float
    loadedFromSymbolBalanceOfWei: int


@credmark.model.describe(slug='example.token-loading',
                         version='1.0',
                         developer='credmark',
                         output=ExampleTokenLoadingOutput)
class ExampleTokenLoading(credmark.model.Model):
    def run(self, input) -> ExampleTokenLoadingOutput:
        cmk = Token(symbol='CMK')
        cmk_holder = Address("0xF6dBFf8433b643bc08cB53BeD6C535c8a57AC912")

        return ExampleTokenLoadingOutput(
            loadedFromAddress=Token(symbol='AAVE'),
            loadedFromSymbol=cmk,
            loadedNativeToken=Token.native_token(),
            loadedFromSymbolPrice=cmk.price_usd,
            loadedFromSymbolTotalSupply=cmk.total_supply().scaled,
            loadedFromSymbolBalanceOf=cmk.balance_of(cmk_holder).scaled,
            loadedFromSymbolBalanceOfWei=cmk.balance_of(cmk_holder)
        )
