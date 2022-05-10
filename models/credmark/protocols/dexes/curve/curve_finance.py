# pylint: disable=locally-disabled, unused-import

import pandas as pd
from typing import List
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError, ModelDataError
from credmark.cmf.types.ledger import TransactionTable
from credmark.dto import DTO, EmptyInput

from credmark.cmf.types import (
    Address,
    Account,
    Accounts,
    Contract,
    Contracts,
    Token,
    Tokens,
)

from web3.exceptions import ABIFunctionNotFound, ContractLogicError


@Model.describe(slug='curve-fi.get-provider',
                version='1.1',
                display_name='Curve Finance - Get Provider',
                description='Get provider contract',
                input=EmptyInput,
                output=Contract)
class CurveFinanceGetProvider(Model):
    CURVE_PROVIDER_ALL_NETWORK = '0x0000000022D53366457F9d5E68Ec105046FC4383'

    def run(self, _) -> Contract:
        provider = Contract(address=Address(self.CURVE_PROVIDER_ALL_NETWORK).checksum)
        return provider


@Model.describe(slug='curve-fi.get-registry',
                version='1.1',
                display_name='Curve Finance - Get Registry',
                description='Query provider to get the registry',
                input=EmptyInput,
                output=Contract)
class CurveFinanceGetRegistry(Model):
    def run(self, _) -> Contract:
        provider = Contract(**self.context.models.curve_fi.get_provider())
        reg_addr = provider.functions.get_registry().call()
        return Contract(address=Address(reg_addr).checksum)


@Model.describe(slug="curve-fi.get-gauge-controller",
                version='1.1',
                display_name="Curve Finance - Get Gauge Controller",
                description="Query the registry for the guage controller")
class CurveFinanceGetGauge(Model):
    def run(self, input):
        registry = Contract(**self.context.models.curve_fi.get_registry())
        gauge_addr = registry.functions.gauge_controller().call()
        return Contract(address=Address(gauge_addr).checksum)


@Model.describe(slug="curve-fi.all-pools",
                version="1.1",
                display_name="Curve Finance - Get all pools",
                description="Query the registry for all pools",
                output=Contracts)
class CurveFinanceAllPools(Model):

    def run(self, input) -> Contracts:
        registry = self.context.run_model('curve-fi.get-registry',
                                          input=EmptyInput(),
                                          return_type=Contract)

        total_pools = registry.functions.pool_count().call()
        pool_contracts = [
            Contract(address=registry.functions.pool_list(i).call())
            for i in range(0, total_pools)]

        return Contracts(contracts=pool_contracts)


class CurveFiPoolInfo(Contract):
    virtualPrice: int
    tokens: Tokens
    tokens_symbol: List[str]
    balances: List[int]
    underlying_tokens: Tokens
    underlying_tokens_symbol: List[str]
    A: int
    is_meta: bool
    name: str
    lp_token_name: str
    pool_token_name: str


class CurveFiPoolInfos(DTO):
    pool_infos: List[CurveFiPoolInfo]


@Model.describe(slug="curve-fi.pool-info",
                version="1.2",
                display_name="Curve Finance Pool Liqudity",
                description="The amount of Liquidity for Each Token in a Curve Pool",
                input=Contract,
                output=CurveFiPoolInfo)
class CurveFinancePoolInfo(Model):
    def run(self, input: Contract) -> CurveFiPoolInfo:
        registry = Contract(**self.context.models.curve_fi.get_registry())

        tokens = Tokens()
        tokens_symbol = []
        underlying = Tokens()
        underlying_symbol = []
        balances = []

        # Equivalent to input.functions.coins(ii).call()
        coins = registry.functions.get_coins(input.address.checksum).call()
        for tok_addr_raw in coins:
            tok_addr = Address(tok_addr_raw)
            if tok_addr != Address.null():
                tok = Token(address=tok_addr.checksum)
                tokens.append(tok)
                try:
                    tokens_symbol.append(tok.symbol)
                except ModelDataError:
                    if tok.address == '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee':
                        tokens_symbol.append('eeeETH')
                    else:
                        raise

        # Equivalent to input.functions.balances(ii).call()
        balances_ret = registry.functions.get_balances(input.address.checksum).call()
        for ii in range(len(tokens_symbol)):
            # tokens.tokens[ii].scaled(balances_ret[ii])
            balances.append(balances_ret[ii])

        # However, input.functions.underlying_coins(ii).call() is empty for some pools
        underlying_coins = registry.functions.get_underlying_coins(input.address.checksum).call()
        for und_addr_raw in underlying_coins:
            und_addr = Address(und_addr_raw)
            if und_addr != Address.null():
                und = Token(address=und_addr.checksum)
                underlying.append(und)
                try:
                    underlying_symbol.append(und.symbol)
                except ModelDataError:
                    if und.address == '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee':
                        underlying_symbol.append('eeeETH')
                    else:
                        raise

        try:
            a = input.functions.A().call()
            virtual_price = input.functions.get_virtual_price().call()
        except Exception as _err:
            virtual_price = (10**18)
            a = 0

        is_meta = registry.functions.is_meta(input.address.checksum).call()
        registry.functions.get_underlying_coins(input.address.checksum).call()

        try:
            name = input.functions.name().call()
        except Exception as _err:
            name = ""

        pool_token_name = ''
        lp_token_name = ''
        try:
            lp_token_addr = Address(input.functions.lp_token().call())
            lp_token_name = Token(address=lp_token_addr.checksum).name
        except ABIFunctionNotFound:
            try:
                provider = self.context.run_model('curve-fi.get-provider',
                                                  input=EmptyInput(),
                                                  return_type=Contract)
                pool_info_addr = Address(provider.functions.get_address(1).call())
                pool_info_contract = Contract(address=pool_info_addr.checksum)
                pool_info = (pool_info_contract.functions.get_pool_info(input.address.checksum)
                             .call())
                lp_token_addr = Address(pool_info[5])
                lp_token_name = Token(address=lp_token_addr.checksum).name
            except ContractLogicError:
                try:
                    pool_token_addr = Address(input.functions.token().call())
                    pool_token = Token(address=pool_token_addr.checksum)
                    pool_token_name = pool_token.name
                except ABIFunctionNotFound:
                    pass

        return CurveFiPoolInfo(**(input.dict()),
                               virtualPrice=virtual_price,
                               tokens=tokens,
                               tokens_symbol=tokens_symbol,
                               balances=balances,
                               underlying_tokens=underlying,
                               underlying_tokens_symbol=underlying_symbol,
                               A=a,
                               is_meta=is_meta,
                               name=name,
                               lp_token_name=lp_token_name,
                               pool_token_name=pool_token_name)


@ Model.describe(slug="curve-fi.all-pools-info",
                 version="1.1",
                 display_name="Curve Finance Pool Liqudity - All",
                 description="The amount of Liquidity for Each Token in a Curve Pool - All",
                 output=CurveFiPoolInfos)
class CurveFinanceTotalTokenLiqudity(Model):

    def run(self, input) -> CurveFiPoolInfos:
        pool_contracts = self.context.run_model('curve-fi.all-pools',
                                                input=EmptyInput(),
                                                return_type=Contracts)
        pool_infos = [
            CurveFiPoolInfo(**self.context.models.curve_fi.pool_info(pool))
            for pool in pool_contracts]

        all_pools_info = CurveFiPoolInfos(pool_infos=pool_infos)

        # (pd.DataFrame((all_pools_info.dict())['pool_infos'])
        # .to_csv(f'tmp/curve-all-info_{self.context.block_number}.csv'))
        return all_pools_info


@ Model.describe(slug="curve-fi.all-gauges",
                 version='1.1',
                 display_name="Curve Finance Gauge List",
                 description="All Gauge Contracts for Curve Finance Pools",
                 input=EmptyInput,
                 output=Contracts)
class CurveFinanceAllGauges(Model):
    def run(self, _) -> Contracts:
        gauge_controller = Contract(**self.context.models.curve_fi.get_gauge_controller())
        gauges = []
        i = 0
        while True:
            address = gauge_controller.functions.gauges(i).call()
            if address == Address.null():
                break
            gauges.append(Contract(address=address))
            i += 1

        return Contracts(contracts=gauges)


@ Model.describe(slug='curve-fi.all-gauge-claim-addresses',
                 version='1.1',
                 input=Contract,
                 output=Accounts)
class CurveFinanceAllGaugeAddresses(Model):

    def run(self, input: Contract) -> Accounts:
        addrs = self.context.ledger.get_transactions(
            columns=[TransactionTable.Columns.FROM_ADDRESS],
            where=f'{TransactionTable.Columns.TO_ADDRESS}=\'{input.address.lower()}\'')
        return Accounts(accounts=[
            Account(address=address)
            for address in
            list(dict.fromkeys([
                a[TransactionTable.Columns.FROM_ADDRESS]
                for a
                in addrs]))])


@ Model.describe(slug='curve-fi.get-gauge-stake-and-claimable-rewards',
                 version='1.1',
                 input=Contract,
                 output=dict)
class CurveFinanceGaugeRewardsCRV(Model):
    def run(self, input: Contract) -> dict:
        yields = []

        all_addrs = Accounts(**self.context.models.curve_fi.all_gauge_claim_addresses(input))
        for addr in all_addrs.accounts:
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


@ Model.describe(slug='curve-fi.gauge-yield',
                 version='1.1',
                 input=Contract,
                 output=dict)
class CurveFinanceAverageGaugeYield(Model):
    CRV_PRICE = 3.0

    def run(self, input: Contract) -> dict:
        """
        presuming that crv has a constant value of $3
        """

        pool_info = self.context.models.curve_fi.pool_info(
            Contract(address=input.functions.lp_token().call()))

        # addrs = self.context.run_model('curve-fi.all-gauge-addresses', input)

        # gauge_input = {
        #     "gaugeAddress": input.address,
        #     "userAddresses": [{"address": a['from_address']} for a in addrs['data']]
        # }

        res = self.context.historical.run_model_historical(
            'curve-fi.get-gauge-stake-and-claimable-rewards',
            window='60 days',
            interval='7 days',
            model_input=input)

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
                            virtual_price = pool_info['virtualPrice'] / (10**18) / (10**18)
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
        return {"pool_info": pool_info, "crv_yield": avg_yield}


@ Model.describe(slug='curve-fi.all-yield',
                 version='1.1',
                 description="Yield from all Gauges",
                 input=EmptyInput,
                 output=dict)
class CurveFinanceAllYield(Model):
    def run(self, _) -> dict:
        gauge_contracts = self.context.run_model('curve-fi.all-gauges',
                                                 input=EmptyInput(),
                                                 return_type=Contracts)

        self.logger.info(f'There are {len(gauge_contracts.contracts)} gauges.')

        res = []
        for gauge in gauge_contracts.contracts:
            yields = self.context.run_model('curve-fi.gauge-yield', gauge)
            self.logger.info(yields)
            res.append(yields)

        return {"results": res}
