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
    Wallet,
)


@credmark.model.describe(slug='var',
                         version='1.0',
                         display_name='Value at Risk',
                         description='Value at Risk',
                         input=Wallet,
                         output=VarOutput)
class Var(credmark.model.Model):

    def run(self, input: VarInput) -> VarOutput:
        """
            Var takes in a portfolio object,
            a list of prices per token into the past,
            a price window,
            and a worst case percentage.

            It calculates the usd value of the portfolio for each of the blockstamps/timestamps.
            It then calculates the change in value over the window period for each timestamp,
            it returns the one that hits the input percentage.
        """

        var = []
        for conf in input.confidence:
            var.append((conf, 100))

        result = VarOutput(var=var)

        return result
