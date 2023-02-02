from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import BlockNumber, Contract
from credmark.cmf.types.series import BlockSeries

from models.credmark.protocols.dexes.curve.curve_finance import CurveFiPoolInfo


@Model.describe(slug="contrib.curve-fi-pool-historical-reserve",
                version="1.2",
                display_name="Curve Finance Pool Liquidity",
                description="gets reserve ratio of stablecoin"
                "pools in Curve for every day in the past year",
                category='protocol',
                subcategory='curve',
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
        res = self.context.run_model(
            'historical.run-model',
            dict(
                model_slug='curve-fi.pool-info',
                window='5 days',
                interval='1 days',
                model_input=input),
            return_type=BlockSeries[CurveFiPoolInfo])

        if res.errors is not None:
            raise ModelRunError(str(res.errors[0].dict()))

        balances = []
        for r in res.series:
            balances.append({
                "name": r.output.name,
                "balances": r.output.balances,
                "address": r.output.address,
                "virtualPrice": r.output.virtualPrice,
                "blocknumber": r.blockNumber,
                "block_time": str(BlockNumber(r.blockNumber).timestamp_datetime)
            })
        return {'balances': balances}
