# pylint: disable=locally-disabled, unused-import

from credmark.cmf.model import Model
from credmark.cmf.types import (Account, Accounts, Address, Contract,
                                Contracts, Portfolio, Position, Price,
                                PriceWithQuote, Some, Token, Tokens)
from credmark.cmf.types.series import BlockSeries


@Model.describe(slug='curve-fi.lp-dist',
                version='1.0',
                input=Contract)
class CurveFinanceLPDist(Model):
    def run(self, input: Contract) -> dict:
        with self.context.ledger.Transaction as q:
            _addrs = q.select(
                columns=[q.FROM_ADDRESS],
                where=q.TO_ADDRESS.eq(input.address)).to_dataframe()['from_address']

        gauageAddress = input.address
        _gauge = Contract(address=gauageAddress)

        dist = []

        for addr in _addrs:
            balanceOf = _gauge.functions.balanceOf(Address(addr).checksum).call()
            dist.append({
                "balanceOf": balanceOf,
                "address": addr
            })
        return {'lp_balance': dist}


@Model.describe(slug='curve-fi.lp-pool-dist',
                version='1.0',
                input=Contract)
class CurveFinanceLPPoolDist(Model):

    def run(self, input: Contract) -> dict:
        with self.context.ledger.Transaction as q:
            _addrs = q.select(
                columns=[q.FROM_ADDRESS],
                where=q.TO_ADDRESS.eq(input.address)).to_dataframe()['from_address']

        pool_address = input.address
        _pool = Contract(address=pool_address)

        dist = []

        for addr in _addrs:
            balanceOf = _pool.functions.balanceOf(Address(addr).checksum).call()
            dist.append({
                "balanceOf": balanceOf,
                "address": addr
            })
        return {'lp_balance': dist}


@Model.describe(slug='curve-fi.historical-lp-dist',
                version='1.0',
                display_name='Curve Finance Pool LP Distribution Historically',
                description='gets the historical dist of LP holders for a given pool',
                input=Contract,
                output=dict)
class CurveFinanceHistoricalLPDist(Model):

    def run(self, input: Contract) -> dict:

        res = self.context.run_model(
            'historical.run-model',
            dict(
                model_slug='curve-fi.lp-dist',
                window='60 days',
                interval='7 days',
                model_input={'address': input.address}
            ),
            return_type=BlockSeries[dict])

        info_i_want = []
        for r in res:
            info_i_want.append({
                "name": r.output['name'],
                "blockNumber": r.blockNumber,
                "address": r.output['from_address'],
                "balanceOf": r.output['balanceOf']
            })

        return {'historical-lp-dist': info_i_want}


@Model.describe(slug='curve-fi.pool-historical-reserve',
                version='1.0',
                display_name='Curve Finance Pool Reserve Ratios',
                description="the historical reserve ratios for a curve pool",
                input=Contract,
                output=dict)
class CurveFinanceReserveRatio(Model):

    def run(self, input: Contract) -> dict:
        # Verify input address can create a contract
        _pool_address = input.address
        _pool_contract = Contract(address=_pool_address.checksum)

        res = self.context.run_model(
            'historical.run-model',
            dict(
                model_slug='curve-fi-pool-info',
                window='365 days',
                interval='7 days',
                model_input=_pool_contract
            ))

        info_i_want = []
        for r in res:
            info_i_want.append({
                "name": r.output['name'],
                "blockNumber": r.blockNumber,
                "balances": r.output['balances'],
                "virtualPrice": r.output['virtualPrice']
            })

        return {'results': info_i_want}
