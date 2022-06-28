# pylint: disable=locally-disabled, unused-import
from typing import List

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import Token, Tokens
from credmark.dto import EmptyInput


@Model.describe(slug='token.stablecoins',
                version='1.0',
                display_name='Token - get list of stable coins on a chain',
                description='A list of stable coins',
                category='protocol',
                tags=['token', 'stablecoin'],
                input=EmptyInput,
                output=Tokens)
class StableCoins(Model):
    STABLECOINS = {
        1: {
            "USDT": '0xdac17f958d2ee523a2206206994597c13d831ec7',
            "USDC": '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
            "DAI": '0x6b175474e89094c44da98b954eedeac495271d0f',
        }
    }

    def run(self, _input: Token) -> Tokens:
        return Tokens(tokens=[Token(address=addr)
                              for addr in self.STABLECOINS[self.context.chain_id].values()])
