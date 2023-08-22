# pylint: disable=locally-disabled, line-too-long
from typing import List

import numpy as np
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Account, Accounts, Address, Contract, Contracts
from credmark.cmf.types.compose import MapInputsOutput
from credmark.cmf.types.series import BlockSeries
from credmark.dto import DTO, EmptyInputSkipTest
from web3.exceptions import (
    ABIFunctionNotFound,
    BadFunctionCallOutput,
    ContractLogicError,
)

from models.credmark.protocols.dexes.curve.curve_meta import CurveAllGaugesOutput, CurveMeta, CurvePool

np.seterr(all='raise')


class CurveGaugeContract(Contract):
    class Config:
        schema_extra = {
            'examples': [{'address': '0x824F13f1a2F29cFEEa81154b46C0fc820677A637'},
                         {'address': '0x72E158d38dbd50A483501c24f792bDAAA3e7D55C'},
                         {'address': '0x11137B10C210b579405c21A07489e28F3c040AB1'},
                         {'address': '0xbFcF63294aD7105dEa65aA58F8AE5BE2D9d0952A'}]
        }


@Model.describe(slug="curve-fi.all-gauges",
                version='1.4',
                display_name="Curve Finance Gauge List",
                description="All Gauge Contracts for Curve Finance Pools",
                category='protocol',
                subcategory='curve',
                output=CurveAllGaugesOutput)
class CurveFinanceAllGauges(Model, CurveMeta):
    def run(self, _) -> CurveAllGaugesOutput:
        gauge_controller = self.get_gauge_controller()
        gauges = []
        lp_tokens = []
        i = 0
        while True:
            addr = gauge_controller.functions.gauges(i).call()
            if Address(addr).is_null():
                break
            gauge_contract = Contract(address=addr)
            gauges.append(gauge_contract)
            i += 1
            try:
                _ = gauge_contract.abi
            except ModelDataError:
                gauge_contract = self.fix_gauge_lp_token(Contract(gauge_contract.address))
            try:
                lp_token_addr = gauge_contract.functions.lp_token().call()
                lp_tokens.append(Account(address=lp_token_addr))
            except (BadFunctionCallOutput, ABIFunctionNotFound, ContractLogicError):
                lp_tokens.append(Account(address=Address.null()))
        return CurveAllGaugesOutput(contracts=gauges,
                                    lp_tokens=Accounts(accounts=lp_tokens))


@Model.describe(slug='curve-fi.gauge-lp-dist',
                version='1.1',
                input=CurveGaugeContract)
class CurveFinanceLPDist(Model):
    def run(self, input: CurveGaugeContract) -> dict:
        with self.context.ledger.Transaction as q:
            _addrs = q.select(
                columns=[q.FROM_ADDRESS],
                where=q.TO_ADDRESS.eq(input.address)).to_dataframe()['from_address']

        gaugeAddress = input.address
        _gauge = Contract(address=gaugeAddress)

        dist = []

        for addr in _addrs:
            balanceOf = _gauge.functions.balanceOf(
                Address(addr).checksum).call()
            dist.append({
                "balanceOf": balanceOf,
                "from_address": addr
            })
        return {'lp_balance': dist}


@Model.describe(slug='curve-fi.historical-gauge-lp-dist',
                version='1.1',
                display_name='Curve Finance Pool LP Distribution Historically',
                description='gets the historical dist of LP holders for a given pool',
                input=CurvePool,
                output=dict)
class CurveFinanceHistoricalLPDist(Model):
    def run(self, input: CurvePool) -> dict:
        res = self.context.run_model(
            'historical.run-model',
            {'model_slug': 'curve-fi.gauge-lp-dist',
             'window': '60 days',
             'interval': '7 days',
             'model_input': {'address': input.address}},
            return_type=BlockSeries[dict])

        info_i_want = []
        for r in res.series:
            info_i_want.append({
                # "name": r.output['lp_balance']['name'],
                "blockNumber": r.blockNumber,
                "lp_balance": r.output['lp_balance']
            })

        return {'historical-lp-dist': info_i_want}


@Model.describe(slug='curve-fi.gauge-claim-addresses',
                version='1.5',
                category='protocol',
                subcategory='curve',
                input=CurveGaugeContract,
                output=Accounts)
class CurveFinanceAllGaugeAddresses(Model):
    def run(self, input: CurveGaugeContract) -> Accounts:
        with self.context.ledger.Transaction as txn:
            addrs = txn.select(
                columns=[txn.FROM_ADDRESS],
                where=txn.TO_ADDRESS.eq(input.address))

            return Accounts(accounts=[
                Account(address=address)
                for address in
                list(dict.fromkeys([
                    a[txn.FROM_ADDRESS]
                    for a
                    in addrs]))])


@Model.describe(slug='curve-fi.get-gauge-stake-and-claimable-rewards',
                version='1.3',
                category='protocol',
                subcategory='curve',
                input=CurveGaugeContract,
                output=dict)
class CurveFinanceGaugeRewardsCRV(Model):
    def run(self, input: CurveGaugeContract) -> dict:
        yields = []

        all_addrs = Accounts(
            **self.context.models.curve_fi.gauge_claim_addresses(input))
        for addr in all_addrs:
            if not addr.address:
                raise ModelRunError(f'Input is invalid, {input}')

            claimable_tokens = input.functions.claimable_tokens(addr.address.checksum).call()
            balanceOf = input.functions.balanceOf(addr.address.checksum).call()
            working_balances = input.functions.working_balances(addr.address.checksum).call()

            yields.append({
                "claimable_tokens": claimable_tokens,
                "balanceOf": balanceOf,
                "working_balances": working_balances,
                "address": addr.address
            })

        return {"yields": yields}


# gaugeAddress = Address('0x72E158d38dbd50A483501c24f792bDAAA3e7D55C')
# _gauge = Contract(address=gaugeAddress.checksum)
# _gauge.set_abi(CURVE_GAUGE_V1_ABI, set_loaded=True)


class CurveGaugeInput(DTO):
    gaugeAddress: Address
    userAddresses: List[Account]


@Model.describe(slug='curve-fi.gauge-yield',
                version='1.6',
                category='protocol',
                subcategory='curve',
                input=CurveGaugeContract,
                output=dict)
class CurveFinanceAverageGaugeYield(Model, CurveMeta):
    CRV_PRICE = 3.0

    def run(self, input: CurveGaugeContract) -> dict:
        """
        presuming that crv has a constant value of $3
        """

        lp_token_addr = input.functions.lp_token().call()

        registry = self.get_registry()

        pool_addr = registry.functions.get_pool_from_lp_token(
            lp_token_addr).call()
        if not Address(pool_addr).is_null():
            pool_info = self.context.run_model(
                'curve-fi.pool-info', Contract(address=pool_addr))
            pool_virtual_price = pool_info['virtualPrice']
        else:
            lp_token = Contract(address=lp_token_addr)
            pool_virtual_price = lp_token.functions.get_virtual_price().call()

        res = self.context.run_model(
            'historical.run-model',
            {'model_slug': 'curve-fi.get-gauge-stake-and-claimable-rewards',
             'window': '60 days',
             'interval': '7 days',
             'model_input': input
             },
            return_type=BlockSeries[dict])

        yields = []
        for idx in range(0, len(res.series) - 1):
            for y1 in res.series[idx].output['yields']:
                if y1['working_balances'] == 0:
                    continue
                if y1['balanceOf'] == 0:
                    continue
                if y1['claimable_tokens'] == 0:
                    continue
                for y2 in res.series[idx + 1].output['yields']:
                    if y1['address'] == y2['address']:
                        if y2['working_balances'] == 0:
                            continue
                        if y2['balanceOf'] == 0:
                            continue
                        if y2['claimable_tokens'] == 0:
                            continue
                        if y1['balanceOf'] == y2['balanceOf']:
                            y2_rewards_value = y2["claimable_tokens"] * self.CRV_PRICE / (10**18)
                            y1_rewards_value = y1["claimable_tokens"] * self.CRV_PRICE / (10**18)
                            virtual_price = pool_virtual_price / (10**18) / (10**18)
                            y2_liquidity_value = y2["balanceOf"] * virtual_price
                            y1_liquidity_value = y1["balanceOf"] * virtual_price
                            new_portfolio_value = y2_rewards_value + y2_liquidity_value
                            old_portfolio_value = y1_rewards_value + y1_liquidity_value
                            if old_portfolio_value > new_portfolio_value:
                                break
                            yields.append(
                                (new_portfolio_value - old_portfolio_value) / old_portfolio_value)
                            break
        if len(yields) == 0:
            return {}
        avg_yield = sum(yields) / len(yields) * (365 * 86400) / (10 * 86400)
        return {"crv_yield": avg_yield}


@Model.describe(slug='curve-fi.all-yield',
                version='1.6',
                description="Yield from all Gauges",
                category='protocol',
                subcategory='curve',
                input=EmptyInputSkipTest,
                output=dict)
class CurveFinanceAllYield(Model):
    def run(self, _) -> dict:
        gauge_contracts = self.context.run_model(
            'curve-fi.all-gauges', {}, return_type=Contracts)

        self.logger.info(f'There are {len(gauge_contracts.contracts)} gauges.')

        res = []
        model_slug = 'curve-fi.gauge-yield'
        all_yields = self.context.run_model(
            slug='compose.map-inputs',
            input={'modelSlug': model_slug,
                   'modelInputs': gauge_contracts.contracts},
            return_type=MapInputsOutput[Contract, dict])

        res = []
        for pool_n, pool_result in enumerate(all_yields):
            if pool_result.output is not None:
                res.append(pool_result)
            elif pool_result.error is not None:
                self.logger.error(pool_result.error)
                raise ModelRunError('Empty result for '
                                    f'{model_slug}({gauge_contracts.contracts[pool_n]}). ' +
                                    pool_result.error.message)
            else:
                raise ModelRunError(
                    'compose.map-inputs: output/error cannot be both None')

        return {"results": res}
