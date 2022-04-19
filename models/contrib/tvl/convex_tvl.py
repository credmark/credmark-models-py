from credmark.cmf.model import Model
from credmark.cmf.types import (Address, Token,Price)



lockedAddress=[
    "0x72a19342e8F1838460eBFCCEf09F6585e32db86E"
]


@Model.describe(
    slug='contrib.cvx-total-value-locked',
    version='1.0',
    display_name='Total Value Locked',
    description='Total Value Locked',
    output=dict
)
class TVL(Model):
    def run(self, input) -> dict:
        address = Address("0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B")
        cvx_token = Token(address=address)

        token_price = self.context.run_model(slug='token.price', input=cvx_token, return_type=Price)

        total_supply = cvx_token.functions.totalSupply().call()

        circulating_supply = total_supply
        for addr in lockedAddress:
            circulating_supply = circulating_supply - \
                cvx_token.functions.balanceOf(
                    addr).call()

        tvl=(circulating_supply*token_price.price) / (total_supply*token_price.price)
        return {"total_value_locked":tvl}