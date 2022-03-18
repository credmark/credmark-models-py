from typing import (
    List
)

import credmark.model

from credmark.types.dto import (
    DTO,
    DTOField
)

from credmark.types import (
    Address,
    Token,
)


class LCRInput(DTO):
    address: Address
    stablecoins: List[str] = DTOField(['USDC', 'USDT', 'DAI'])
    cashflow_shock: float = DTOField(1e10)

    class Config:
        schema_extra = {
            'examples': [{'address': '0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0',
                          'cashflow_shock': 1e10}]
        }


@credmark.model.describe(slug='finance.lcr',
                         version='1.0',
                         display_name='Liquidity Coverage Ratio',
                         description='A simple LCR model',
                         input=LCRInput)
class Var(credmark.model.Model):

    def run(self, input: LCRInput) -> dict:
        """
            LCR takes in
            - an account,
            - list of stablecoin token names, and
            - cashflow shock

            It calculates the total holding of stablecoins (pegged to USD with 1:1),
            and LCR is the ratio between the total holding and the max cashflow_shock.
        """

        account = input.address

        sb_sum = 0
        sb_dict = {}
        for sb in input.stablecoins:
            ct = Token(symbol=sb)
            bal = ct.balance_of(account).scaled
            sb_sum += bal
            sb_dict[sb] = bal

        return {'account': account, 'holding': sb_dict, 'total': sb_sum, 'lcr': sb_sum / input.cashflow_shock}
