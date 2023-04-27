from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import (Contract, Maybe, NativeToken, Network,
                                PriceWithQuote, Token)

from models.dtos.price import PriceInput


@Model.describe(slug='price.one-inch',
                version='0.6',
                display_name='Token Price - Spot Aggregator',
                description='Returns price in Eth for Token from 1Inch',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price', '1inch'],
                input=PriceInput,
                output=Maybe[PriceWithQuote])
class PriceOneInch(Model):
    OFFCHAIN_ADDRESS = {
        Network.Mainnet: '0x07D91f5fb9Bf7798734C3f606dB065549F6893bb'
    }

    def run(self, input: PriceInput) -> Maybe[PriceWithQuote]:
        try:
            if isinstance(input.base, Token):
                addr = self.OFFCHAIN_ADDRESS[self.context.network]
                offchain_contract = Contract(address=addr)
                eth = NativeToken()
                p = (offchain_contract.functions.getRateToEth(input.base.address.checksum, True)
                     .call() / (10 ** (eth.decimals+eth.decimals - input.base.decimals)))
                # _p2 = offchain_contract.functions.getRateToEth(input.address, False).call(
                # ) / (10 ** (eth.decimals+eth.decimals - input.decimals))
                if p != 0:
                    p_weth = self.context.run_model('price.quote',
                                                    {'base': 'WETH',
                                                        'quote': input.quote},
                                                    return_type=PriceWithQuote)
                    return Maybe(just=PriceWithQuote.eth(price=p, src=self.slug).cross(p_weth))
        except ModelRunError:
            pass

        return Maybe.none()
