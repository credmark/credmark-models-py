import json

from credmark.cmf.model import Model

from credmark.cmf.types import (
    Portfolio,
    Token,
    Position,
    PriceList,
)

from models.credmark.algorithms.value_at_risk.dto import (
    HistoricalPriceInput,
    VaRHistoricalInput,
    ContractVaRInput,
)


@Model.describe(slug='finance.example-historical-price',
                version='1.1',
                display_name='Value at Risk - Get Price Historical',
                description='Feed a mock historical price list',
                input=HistoricalPriceInput,
                output=PriceList)
class VaRPriceHistorical(Model):
    """
    Generate example historical prices uses dummy data of range of 1 to window + 1.
    The priceList is assumed to be sorted in descending order in time.
    """

    def run(self, input: HistoricalPriceInput) -> PriceList:
        token = input.token
        _w_k, w_i = self.context.historical.parse_timerangestr(input.window)

        return PriceList(
            prices=list(range(1, w_i+2)),
            tokenAddress=token.address,
            src=self.slug
        )


@Model.describe(slug='finance.example-var-contract',
                version='1.1',
                display_name='Value at Risk',
                description='Example of implementing VaR for a portfolio',
                input=ContractVaRInput,
                output=dict)
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
    '{"asOf": "2022-02-17", "window": "30 days", "interval": 3, "confidences": [0.01,0.05]}' \
    -l finance.example-var-contract,finance.example-historical-price,finance.var-engine-historical \
    -b 14234904 --format_json
    """

    def run(self, input: ContractVaRInput) -> dict:
        # Get the portfolio as of the input.asOf. Below is example input.
        portfolio = Portfolio(
            positions=[
                Position(asset=Token(symbol='AAVE'), amount=100),
                Position(asset=Token(symbol='USDC'), amount=100),
                Position(asset=Token(symbol='USDC'), amount=1)]
        )

        pls = []
        pl_assets = set()
        for pos in portfolio:
            if pos.asset.address not in pl_assets:
                historical_price_input = HistoricalPriceInput(token=pos.asset,
                                                              window=input.window,
                                                              asOf=input.asOf)
                # json.loads(dto.json()) is to marshal date type to JSON
                pl = self.context.run_model(slug='finance.example-historical-price',
                                            input=json.loads(historical_price_input.json()),
                                            return_type=PriceList)
                pls.append(pl)
                pl_assets.add(pos.asset.address)

        var_input = VaRHistoricalInput(
            portfolio=portfolio,
            priceLists=pls,
            interval=input.interval,
            confidences=input.confidences,
        )

        return self.context.run_model(slug='finance.var-engine-historical',
                                      input=var_input,
                                      return_type=dict)
