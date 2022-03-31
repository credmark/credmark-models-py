from credmark.cmf.model import Model
from credmark.cmf.types import Token

lockedAddresses = [
    "0xCbF507C87f19B58fB719B65697Fb7fA84D682aA9",
    "0xCA9bb8A10B2C0FB16A18eDae105456bf7e91B041",
    "0x70371C6D23A26Df7Bf0654C47D69ddE9000013E7",
    "0x0f8d3D79f5Fb9EDFceFF399F056c996eb9b89C67",
    "0xC2560D7D2cF12f921193874cc8dfBC4bb162b7cb",
    "0xdb9DCecbA3f21e2aa53897a05A92F89209731b68",
    "0x5CE367c907a119afa25f4DBEe4f5B4705C802Df5",
    "0x46d812De7EF3cA2E3c1D8EfFb496F070b2202DFF",
    "0x02bCb9675727ADe60243c3d467A3bF152142698b",
    "0x654958393B7E54f1e2e51f736a14b9d26D00Eb1e"
]


@Model.describe(slug='cmk.total-supply',
                version='1.0',
                display_name='CMK Total Supply',
                description='This is the Total Supply of CMK',
                developer='Credmark')
class TotalSupplyCMK(Model):

    def run(self, input) -> dict:
        cmk_token = Token(symbol='CMK')
        total_supply = cmk_token.functions.totalSupply().call()
        return {'total_supply': total_supply}


@Model.describe(slug='cmk.circulating-supply',
                version='1.0',
                display_name='CMK Circulating Supply',
                description='This is the Circulating Supply of CMK.',
                developer='Credmark')
class CirculatingCMK(Model):

    def run(self, input) -> dict:

        supply = self.context.run_model("cmk.total-supply")['total_supply']
        cmk_token = Token(symbol='CMK')

        for addr in lockedAddresses:
            supply = supply - \
                cmk_token.functions.balanceOf(
                    addr).call()

        return {'result': supply}
