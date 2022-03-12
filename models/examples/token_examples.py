from pydoc import describe
import credmark.model
from credmark.types import Token

from typing import (
    Dict,
    Union
)


@credmark.model.describe(slug='example.token-loading', version='1.0')
class ExampleTokenLoading(credmark.model.Model):
    def run(self, input) -> Dict[str, Union[Token, float]]:

        res = {}
        loaded_from_address = self.context.run_model(
            'example.token-input',
            Token(address='0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9'), return_type=Token)
        res['loadedFromAddress'] = loaded_from_address
        res['loadedFromSymbol'] = self.context.run_model('example.token-input',
                                                         Token(symbol='CMK'))
        # res['loadedFromSymbolPrice'] = Token(symbol='CMK').price_usd
        res['loadedNativeToken'] = Token.native_token()
        #res['loadedNativePrice'] = res['loadedNativeToken'].price_usd
        return res


@credmark.model.describe(slug='example.token-input', version='1.0', input=Token, output=Token)
class ExampleTokenInput(credmark.model.Model):
    def run(self, input: Token) -> Token:
        return input
