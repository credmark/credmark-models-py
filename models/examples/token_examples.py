from pydoc import describe
import credmark.model
from credmark.types.data.token import Token


@credmark.model.describe(slug='example-token-loading', version='1.0')
class ExampleTokenLoading(credmark.model.Model):
    def run(self, input) -> dict:
        res = {}
        res['loadedFromAddress'] = self.context.run_model(
            'example-token-input', {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"})
        res['loadedFromSymbol'] = self.context.run_model('example-token-input', {"symbol": "CMK"})

        res['loadedFromSymbolPrice'] = Token(symbol='CMK').price_usd
        return res


@credmark.model.describe(slug='example-token-input', version='1.0', input=Token)
class ExampleTokenInput(credmark.model.Model):
    def run(self, input: Token) -> Token:
        return input
