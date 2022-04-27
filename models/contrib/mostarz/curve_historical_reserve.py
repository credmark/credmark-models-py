from typing import List
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types.ledger import TransactionTable

from credmark.dto import (
    DTO,
    EmptyInput,
)

from credmark.cmf.types import (
    Address,
    Account,
    Accounts,
    Contract,
    Contracts,
    Token,
    Tokens,
)


@Model.describe(slug="contrib.curve-fi-pool-historical-reserve",
                version="1.1",
                display_name="Curve Finance Pool Liqudity",
                description="The amount of Liquidity for Each Token in a Curve Pool",
                input=Contract,
                output=dict)
class CurveFinanceHistoricalReserve(Model):
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
