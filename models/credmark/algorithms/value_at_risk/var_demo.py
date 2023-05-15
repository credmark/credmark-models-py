from credmark.cmf.model import Model
from credmark.cmf.types import Portfolio, Position, PriceList, Token
from credmark.dto import DTO

from models.credmark.algorithms.value_at_risk.dto import (
    VaRHistoricalInput,
    VaRHistoricalOutput,
    VaRInput,
)


class ExampleHistoricalPriceInput(DTO):
    token: Token
    window: str  # e.g. '30 day'

    class Config:
        schema_extra = {
            'description': ('Returns a list of prices from 1 to window + 1 '
                            '(1 more input as we need to calculate return)'),
            'examples': [{
                'prices': [float(i) for i in range(1, 31+1)],
                'tokenAddress': '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9',
                'src': 'finance.example-historical-price'
            }]
        }


@Model.describe(slug='finance.example-historical-price',
                version='1.2',
                display_name='Value at Risk - Get Price Historical',
                description='Feed a mock historical price list',
                category='example',
                input=ExampleHistoricalPriceInput,
                output=PriceList)
class VaRPriceHistorical(Model):
    """
    Generate example historical prices uses dummy data of range of 1 to window + 1.
    The priceList is assumed to be sorted in descending order in time.
    """

    def run(self, input: ExampleHistoricalPriceInput) -> PriceList:
        token = input.token
        _w_k, w_i = self.context.historical.parse_timerangestr(input.window)

        res = PriceList(
            prices=list(range(1, w_i+2)),
            tokenAddress=token.address,
            src=self.slug
        )

        return res


@Model.describe(slug='finance.example-var-contract',
                version='1.4',
                display_name='Value at Risk',
                description='Example of implementing VaR for a portfolio',
                category='example',
                subcategory='financial',
                tags=['var'],
                input=VaRInput,
                output=VaRHistoricalOutput)
class DemoContractVaR(Model):
    """
    For below Demo VaR of 100 Aave + 100 USDC + 1 USDC
    Token price is assumed $1 each.
    Token price series is 1...31
    Windows is 30 days
    Interval is 3 days
    We shall have -142.6095 (0.01) -113.565 (0.05)

    # Demo command
    credmark-dev run finance.example-var-contract --input \
    '{"window": "30 days", "interval": 3, "confidence": 0.01}' \
    -l finance.example-var-contract,finance.example-historical-price,finance.var-engine-historical \
    -b 14234904 --format_json
    """

    def run(self, input: VaRInput) -> VaRHistoricalOutput:
        portfolio = Portfolio(
            positions=[
                Position(asset=Token(symbol='AAVE'), amount=100),
                Position(asset=Token(symbol='USDC'), amount=100),
                Position(asset=Token(symbol='USDC'), amount=1)]
        )

        pls = []
        pl_assets = set()
        for position in portfolio:
            if position.asset.address not in pl_assets:
                historical_price_input = ExampleHistoricalPriceInput(token=position.asset,
                                                                     window=input.window)
                pl = self.context.run_model(slug='finance.example-historical-price',
                                            input=historical_price_input,
                                            return_type=PriceList)
                pls.append(pl)
                pl_assets.add(position.asset.address)

        var_input = VaRHistoricalInput(
            portfolio=portfolio,
            priceLists=pls,
            interval=input.interval,
            confidence=input.confidence
        )

        return self.context.run_model(slug='finance.var-engine-historical',
                                      input=var_input,
                                      return_type=VaRHistoricalOutput)
