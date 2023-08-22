# pylint: disable=locally-disabled

from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract

from models.credmark.protocols.dexes.curve.curve_finance import CurvePool


class CurvePoolSkipTest(CurvePool):
    class Config:
        schema_extra = {
            'skip_test': True
        }


@Model.describe(slug='curve-fi.lp-pool-dist',
                version='1.0',
                input=CurvePoolSkipTest)
class CurveFinanceLPPoolDist(Model):

    def run(self, input: CurvePool) -> dict:
        with self.context.ledger.Transaction as q:
            _addrs = q.select(
                columns=[q.FROM_ADDRESS],
                where=q.TO_ADDRESS.eq(input.address)).to_dataframe()['from_address']

        pool_address = input.address
        _pool = Contract(address=pool_address)

        dist = []

        for addr in _addrs:
            balanceOf = _pool.functions.balanceOf(
                Address(addr).checksum).call()
            dist.append({
                "balanceOf": balanceOf,
                "address": addr
            })
        return {'lp_balance': dist}
