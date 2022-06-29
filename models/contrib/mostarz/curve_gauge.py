
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import Accounts, Contract


@ Model.describe(slug='contrib.curve-fi-get-gauge-amounts',
                 version='1.2',
                 category='protocol',
                 subcategory='curve',
                 input=Contract,
                 output=dict)
class CurveFinanceGaugeAmounts(Model):
    def run(self, input: Contract) -> dict:
        balances = []

        all_addrs = Accounts(**self.context.models.curve_fi.all_gauge_claim_addresses(input))
        for addr in all_addrs.accounts:
            if not addr.address:
                raise ModelRunError(f'Input is invalid, {input}')

            balanceOf = input.functions.balanceOf(addr.address.checksum).call()

            balances.append({
                "balanceOf": balanceOf,
                "address": addr.address
            })
        return {"balances": balances}
