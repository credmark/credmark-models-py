from credmark.cmf.model import Model
from credmark.cmf.types import Address, Token


@Model.describe(
    slug='contrib.curve-crv-lockup',
    display_name='ratio of CRV in circulation vs vesting contract',
    description=("ratio of CRV tokens locked up in vesting contract "
                 "and vote escrow against total supply"),
    version='1.0',
    developer='exa256',
    category='protocol',
    subcategory='curve',
    output=dict
)
class CurveFinanceVeCRVLockup(Model):
    CRV_ADDRESS = {
        1: Address('0xD533a949740bb3306d119CC777fa900bA034cd52')
    }

    veCRV_ADDRESS = {
        1: Address('0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2')
    }

    vestCRV_ADDRESS = {
        1: Address('0xd2D43555134dC575BF7279F4bA18809645dB0F1D')
    }

    def run(self, input):
        crv_token = Token(address=self.CRV_ADDRESS[self.context.chain_id])

        crv_total_supply = crv_token.total_supply
        crv_locked = crv_token.functions.balanceOf(
            self.veCRV_ADDRESS[self.context.chain_id]).call()
        crv_vested = crv_token.functions.balanceOf(
            self.vestCRV_ADDRESS[self.context.chain_id]).call()

        return {
            'total_supply': crv_token.scaled(crv_total_supply),
            'crv_locked': crv_token.scaled(crv_locked),
            'crv_vested': crv_token.scaled(crv_vested),
            'lockup_ratio': (crv_locked + crv_vested) / crv_total_supply
        }
