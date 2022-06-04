from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract, Token
from credmark.cmf.types import (
    Contract,
    BlockNumber
)

@Model.describe(
    slug='contrib.curve-crv-lockup',
    display_name='ratio of CRV in circulation vs vesting contract',
    description="ratio of CRV tokens locked up in vesting contract and vote escrow against total supply",
    version='1.0',
    developer='exa256',
    output=dict
)
class CurveFinanceVeCRVLockup(Model):
    def run(self, input):
        crv_token = Token(address=Address("0xD533a949740bb3306d119CC777fa900bA034cd52"))
        decimals = crv_token.decimals
        total_supply = crv_token.total_supply
        crv_locked = crv_token.functions.balanceOf("0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2").call()
        crv_vested = crv_token.functions.balanceOf("0xd2D43555134dC575BF7279F4bA18809645dB0F1D").call()
        
        return {
            'total_supply': crv_token.scaled(total_supply),
            'crv_locked': crv_token.scaled(crv_locked),
            'crv_vested': crv_token.scaled(crv_vested),
            'lockup_ratio': (crv_token.scaled(crv_locked) + crv_token.scaled(crv_vested))/ crv_token.scaled(total_supply)
        }