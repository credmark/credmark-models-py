from credmark.cmf.model import Model
from credmark.cmf.types import (
    Contract,
)


@Model.describe(slug="contrib.curve-fi-pool-historical-reserve",
                version="1.1",
                display_name="Curve Finance Pool Liqudity",
                description="gets reserve ratio of stablecoin"
                "pools in Curve for every day in the past year",
                input=Contract,
                output=dict)
class CurveFinanceHistoricalReserve(Model):
    """
    INSTRUCTIONS
    1. go to the curve.fi and find the pool you want
    2. click on the pool and scroll to the bottom
    3. click on "POOL ADDRESS",  you will be sent to Etherscan
    4. copy that address and enter it

    """

    def run(self, input: Contract) -> dict:
        res = self.context.historical.run_model_historical(
            'curve-fi.pool-info',
            window='365 days',
            interval='1 days',
            model_input=input)

        balances = []
        for r in res:

            balances.append({
                "name": r.output['name'],
                "balances": r.output['balances'],
                "address": r.output['address'],
                "virtualPrice": r.output['virtualPrice'],
                "blocknumber": r.blockNumber
            })

        return {'balances': balances}
