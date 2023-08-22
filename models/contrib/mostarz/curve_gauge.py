
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelInputError
from credmark.cmf.types import Accounts, Contract

from models.credmark.protocols.dexes.curve.curve_gauge import CurveGaugeContract


@Model.describe(slug='contrib.curve-fi-get-gauge-amounts',
                version='1.3',
                category='protocol',
                subcategory='curve',
                input=CurveGaugeContract,
                output=dict)
class CurveFinanceGaugeAmounts(Model):
    def run(self, input: Contract) -> dict:
        balances = []

        all_addrs = Accounts(
            **self.context.models.curve_fi.gauge_claim_addresses(input))
        for addr in all_addrs:
            if not addr.address:
                raise ModelInputError(f'Input is invalid, {input}')

            balanceOf = input.functions.balanceOf(addr.address.checksum).call()

            balances.append({
                "balanceOf": balanceOf,
                "address": addr.address
            })
        return {"balances": balances}
