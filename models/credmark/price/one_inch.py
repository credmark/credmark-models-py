from credmark.cmf.model import Model
from credmark.cmf.types import (Contract, Maybe, NativeToken, Network, Price,
                                Token)


@Model.describe(slug='price.one-inch',
                version='0.1',
                display_name='Token Price - Spot Aggregator',
                description='Returns price in Eth for Token from 1Inch',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price', '1inch'],
                input=Token,
                output=Maybe[Price])
class PriceOneInch(Model):
    OFFCHAIN_ADDRESS = {
        Network.Mainnet: '0x07D91f5fb9Bf7798734C3f606dB065549F6893bb'
    }

    def run(self, input: Token) -> Maybe[Price]:
        addr = self.OFFCHAIN_ADDRESS[self.context.network]
        offchain_contract = Contract(address=addr)
        eth = NativeToken()
        p = offchain_contract.functions.getRateToEth(input.address, True).call(
        ) / (10 ** (eth.decimals+eth.decimals - input.decimals))
        # _p2 = offchain_contract.functions.getRateToEth(input.address, False).call(
        # ) / (10 ** (eth.decimals+eth.decimals - input.decimals))
        if p == 0:
            return Maybe.none()
        else:
            return Maybe(just=Price(price=p, src=self.slug))
