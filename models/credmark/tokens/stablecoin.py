# pylint: disable=locally-disabled

from credmark.cmf.model import Model
from credmark.cmf.types import Address, Network, Tokens


@Model.describe(slug='token.stablecoins',
                version='1.0',
                display_name='Token - get list of stable coins on a chain',
                description='A list of stable coins',
                category='protocol',
                tags=['token', 'stablecoin'],
                output=Tokens)
class StableCoins(Model):
    STABLECOINS = {
        Network.Mainnet: {
            "USDT": '0xdac17f958d2ee523a2206206994597c13d831ec7',
            "USDC": '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
            "DAI": '0x6b175474e89094c44da98b954eedeac495271d0f',
        }
    }

    def run(self, _) -> Tokens:
        return Tokens.from_addresses(
            [Address(addr) for addr in self.STABLECOINS[self.context.network].values()])
