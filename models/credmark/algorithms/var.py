from typing import List
import credmark.model
from credmark.types.dto import DTO
from credmark.types import Portfolio, Price, Address


class PriceList(DTO):
    price: Price
    token: Address


class VarInputDTO(DTO):
    portfolio: Portfolio
    prices: List[PriceList]
    window: int
    percentage: float


@credmark.model.describe(slug='var',
                         version='1.0',
                         display_name='Value at Risk',
                         description='Value at Risk',
                         input=VarInputDTO)
class Var(credmark.model.Model):

    def run(self, input) -> dict:
        """
            Var takes in a portfolio object,
            a list of prices per token into the past,
            a price window,
            and a worst case percentage.

            It calculates the usd value of the portfolio for each of the blockstamps/timestamps.
            It then calculates the change in value over the window period for each timestamp,
            it returns the one that hits the input percentage.

        """
        result = {'value': 'not yet implemented'}

        return result
