from typing import (
    List,
    Tuple,
)
import credmark.model
from credmark.types.dto import DTO, DTOField
from credmark.types import (
    Portfolio,
    Price,
    Address,
)


class LCRInput(DTO):
    address: Address
    stablecoins: List[str] = DTOField(['USDC', 'USDT', 'DAI'])
    shock: float


@credmark.model.describe(slug='lcr',
                         version='1.0',
                         display_name='Liquidity Coverage Ratio',
                         description='A simple LCR model',
                         input=LCRInput)
class Var(credmark.model.Model):

    def run(self, input: LCRInput) -> dict:
        """
            Var takes in a portfolio object,
            a list of prices per token into the past,
            a price window,
            and a worst case percentage.

            It calculates the usd value of the portfolio for each of the blockstamps/timestamps.
            It then calculates the change in value over the window period for each timestamp,
            it returns the one that hits the input percentage.
        """

        return {}
