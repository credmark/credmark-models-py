# pylint: disable=locally-disabled, unused-import

from datetime import timedelta
from typing import List, Union

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import (Account, Accounts, Address, Contract,
                                Contracts, Portfolio, Position, Price, Token,
                                Tokens)
from credmark.cmf.types.compose import MapInputsOutput
from credmark.cmf.types.ledger import TransactionTable
from credmark.dto import DTO, EmptyInput
from models.dtos.price import Prices
from models.dtos.tvl import TVLInfo
from web3.exceptions import ABIFunctionNotFound, ContractLogicError


class CurveFiPoolInfoToken(Contract):
    tokens: Tokens
    tokens_symbol: List[str]
    balances: List[float]  # exclude fee
    balances_token: List[float]  # include fee
    admin_fees: List[float]
    underlying: Tokens
    underlying_symbol: List[str]
    name: str
    lp_token_name: str
    lp_token_addr: Address
    pool_token_name: str
    pool_token_addr: Address


class CurveFiPoolInfo(CurveFiPoolInfoToken):
    token_prices: List[Price]
    virtualPrice: int
    A: int
    chi: float
    ratio: float
    is_meta: bool


class CurveFiPoolInfos(DTO):
    pool_infos: List[CurveFiPoolInfo]


@ Model.describe(slug='curve-fi.get-provider',
                 version='1.2',
                 display_name='Curve Finance - Get Provider',
                 description='Get provider contract',
                 input=EmptyInput,
                 output=Contract)
class CurveFinanceGetProvider(Model):
    CURVE_PROVIDER_ALL_NETWORK = '0x0000000022D53366457F9d5E68Ec105046FC4383'

    def run(self, _) -> Contract:
        provider = Contract(address=Address(self.CURVE_PROVIDER_ALL_NETWORK).checksum)
        return provider


@ Model.describe(slug='curve-fi.get-registry',
                 version='1.2',
                 display_name='Curve Finance - Get Registry',
                 description='Query provider to get the registry',
                 input=EmptyInput,
                 output=Contract)
class CurveFinanceGetRegistry(Model):
    def run(self, _) -> Contract:
        provider = Contract(**self.context.models.curve_fi.get_provider())
        reg_addr = provider.functions.get_registry().call()
        return Contract(address=Address(reg_addr).checksum)


@ Model.describe(slug="curve-fi.get-gauge-controller",
                 version='1.2',
                 display_name="Curve Finance - Get Gauge Controller",
                 description="Query the registry for the guage controller",
                 input=EmptyInput,
                 output=Contract)
class CurveFinanceGetGauge(Model):
    def run(self, _):
        registry = Contract(**self.context.models.curve_fi.get_registry())
        gauge_addr = registry.functions.gauge_controller().call()
        return Contract(address=Address(gauge_addr))


@ Model.describe(slug="curve-fi.all-pools",
                 version="1.2",
                 display_name="Curve Finance - Get all pools",
                 description="Query the registry for all pools",
                 output=Contracts)
class CurveFinanceAllPools(Model):
    def run(self, _) -> Contracts:
        registry = self.context.run_model('curve-fi.get-registry',
                                          input=EmptyInput(),
                                          return_type=Contract)

        total_pools = registry.functions.pool_count().call()
        pool_contracts = [
            Contract(address=registry.functions.pool_list(i).call())
            for i in range(0, total_pools)]

        return Contracts(contracts=pool_contracts)


@Model.describe(slug="curve-fi.pool-info-tokens",
                version="1.1",
                display_name="Curve Finance Pool - Tokens",
                description="The amount of Liquidity for Each Token in a Curve Pool",
                input=Contract,
                output=CurveFiPoolInfoToken)
class CurveFinancePoolInfoTokens(Model):
    @staticmethod
    def check_token_address(addrs):
        token_list = Tokens()
        symbols_list = []

        for addr in addrs:
            tok_addr = Address(addr)
            if tok_addr != Address.null():
                tok = Token(address=tok_addr.checksum)
                symbols_list.append(tok.symbol)
                token_list.append(tok)
        return token_list, symbols_list

    def run(self, input: Contract) -> CurveFiPoolInfoToken:
        registry = Contract(**self.context.models.curve_fi.get_registry())

        balances = []

        # Equivalent to input.functions.balances(ii).call()
        try:
            # Use Registry
            balances_tokens = registry.functions.get_balances(input.address.checksum).call()

            # Equivalent to input.functions.coins(ii).call()
            coins = registry.functions.get_coins(input.address.checksum).call()
            tokens, tokens_symbol = self.__class__.check_token_address(coins)

            # However, input.functions.underlying_coins(ii).call() is empty for some pools
            underlying_coins = (registry.functions.get_underlying_coins(input.address.checksum)
                                .call())
            underlying, underlying_symbol = self.__class__.check_token_address(underlying_coins)
            balances_raw = balances_tokens[:len(tokens_symbol)]

            balances = [t.scaled(bal) for bal, t in zip(balances_raw, tokens)]

        except ContractLogicError:
            try:
                minter_addr = input.functions.minter().call()
                return self.context.run_model(self.slug,
                                              input=Contract(address=Address(minter_addr)),
                                              return_type=CurveFiPoolInfo)
            except ABIFunctionNotFound:
                pass

            tokens = Tokens()
            tokens_symbol = []
            underlying = Tokens()
            underlying_symbol = []
            for i in range(8):
                try:
                    tok_addr = Address(input.functions.coins(i).call())
                    token = Token(address=tok_addr)
                    tokens.append(token)
                    tokens_symbol.append(token.symbol)
                    balances.append(token.scaled(input.functions.balances(i).call()))
                    try:
                        und = input.functions.underlying_coins(i).call()
                        underlying.append(und)
                        underlying_symbol.append(und.symbol)
                    except (ABIFunctionNotFound, ContractLogicError):
                        pass
                except ContractLogicError:
                    break

        balances_token = [t.balance_of_scaled(input.address) for t in tokens]

        admin_fees = [bal_token-bal for bal, bal_token in zip(balances, balances_token)]

        try:
            name = input.functions.name().call()
        except Exception as _err:
            name = ""

        lp_token_addr = Address.null()
        lp_token_name = ''
        try:
            lp_token_addr = Address(registry.functions.get_lp_token(input.address).call())
        except ABIFunctionNotFound:
            try:
                lp_token_addr = Address(input.functions.lp_token().call())
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
                except ContractLogicError:
                    pass

        if lp_token_addr != Address.null():
            lp_token = Token(address=lp_token_addr.checksum)
            lp_token_name = lp_token.name

        pool_token_addr = Address.null()
        pool_token_name = ''
        try:
            pool_token_addr = Address(input.functions.token().call())
            pool_token = Token(address=pool_token_addr.checksum)
            pool_token_name = pool_token.name
        except ABIFunctionNotFound:
            pass

        return CurveFiPoolInfoToken(**(input.dict()),
                                    tokens=tokens,
                                    tokens_symbol=tokens_symbol,
                                    balances=balances,
                                    balances_token=balances_token,
                                    admin_fees=admin_fees,
                                    underlying=underlying,
                                    underlying_symbol=underlying_symbol,
                                    name=name,
                                    lp_token_name=lp_token_name,
                                    lp_token_addr=lp_token_addr,
                                    pool_token_name=pool_token_name,
                                    pool_token_addr=pool_token_addr
                                    )


@Model.describe(slug="curve-fi.pool-info",
                version="1.14",
                display_name="Curve Finance Pool Liqudity",
                description="The amount of Liquidity for Each Token in a Curve Pool",
                input=Contract,
                output=CurveFiPoolInfo)
class CurveFinancePoolInfo(Model):
    def run(self, input: Contract) -> CurveFiPoolInfo:
        registry = Contract(**self.context.models.curve_fi.get_registry())
        pool_info = self.context.run_model('curve-fi.pool-info-tokens',
                                           input,
                                           return_type=CurveFiPoolInfoToken)

        token_prices = self.context.run_model(
            'price.quote-multiple',
            input={'inputs': [{'base': tok} for tok in pool_info.tokens]},
            return_type=Prices).prices

        np_balance = np.array(pool_info.balances_token) * np.array([p.price for p in token_prices])
        n_asset = np_balance.shape[0]
        product_balance = np_balance.prod()
        avg_balance = np_balance.mean()

        # Calculating ratio, this gives information about peg
        ratio = product_balance / np.power(avg_balance, n_asset)

        try:
            virtual_price = input.functions.get_virtual_price().call()
        except Exception as _err:
            virtual_price = (10**18)

        try:
            pool_A = input.functions.A().call()
        except Exception as _err:
            pool_A = 0

        # Calculating 'chi'
        chi = pool_A * ratio

        is_meta = registry.functions.is_meta(input.address.checksum).call()

        return CurveFiPoolInfo(**(pool_info.dict()),
                               token_prices=token_prices,
                               virtualPrice=virtual_price,
                               A=pool_A,
                               ratio=ratio,
                               chi=chi,
                               is_meta=is_meta)


@Model.describe(slug="curve-fi.pool-tvl",
                version="1.1",
                display_name="Curve Finance Pool - TVL",
                description="Total amount of TVL",
                input=Contract,
                output=TVLInfo)
class CurveFinancePoolTVL(Model):
    def run(self, input: Contract) -> TVLInfo:
        pool_info = self.context.run_model('curve-fi.pool-info',
                                           input=input,
                                           return_type=CurveFiPoolInfo)
        positions = []
        tvl = 0.0
        for tok, tok_price, bal in zip(pool_info.tokens.tokens,
                                       pool_info.token_prices,
                                       pool_info.balances):
            positions.append(Position(amount=bal, asset=tok))
            tvl += bal * tok_price.price

        pool_name = pool_info.name
        if pool_info.name == '':
            pool_name = pool_info.lp_token_name
            if pool_name == '':
                pool_name = pool_info.pool_token_name

        tvl_info = TVLInfo(
            address=input.address,
            name=pool_name,
            portfolio=Portfolio(positions=positions),
            tokens_symbol=pool_info.tokens_symbol,
            prices=pool_info.token_prices,
            tvl=tvl
        )

        return tvl_info


@Model.describe(slug="curve-fi.all-pools-info",
                version="1.2",
                display_name="Curve Finance Pool Liqudity - All",
                description="The amount of Liquidity for Each Token in a Curve Pool - All",
                output=CurveFiPoolInfos)
class CurveFinanceTotalTokenLiqudity(Model):
    def run(self, _) -> CurveFiPoolInfos:
        pool_contracts = self.context.run_model('curve-fi.all-pools',
                                                input=EmptyInput(),
                                                return_type=Contracts)
        pool_infos = [
            CurveFiPoolInfo(**self.context.models.curve_fi.pool_info(pool))
            for pool in pool_contracts]

        all_pools_info = CurveFiPoolInfos(pool_infos=pool_infos)

        # (pd.DataFrame((all_pools_info.dict())['pool_infos'])
        #    .to_csv(f'tmp/curve-all-info_{self.context.block_number}.csv'))
        return all_pools_info


@ Model.describe(slug="curve-fi.all-gauges",
                 version='1.2',
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
                 version='1.2',
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
                 version='1.2',
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
                 version='1.2',
                 input=Contract,
                 output=dict)
class CurveFinanceAverageGaugeYield(Model):
    CRV_PRICE = 3.0

    def run(self, input: Contract) -> dict:
        """
        presuming that crv has a constant value of $3
        """

        lp_token_addr = input.functions.lp_token().call()

        registry = self.context.run_model('curve-fi.get-registry',
                                          input=EmptyInput(),
                                          return_type=Contract)
        pool_addr = registry.functions.get_pool_from_lp_token(lp_token_addr).call()
        if pool_addr != Address.null():
            pool_info = self.context.models.curve_fi.pool_info(Contract(address=pool_addr))
            pool_virtual_price = pool_info['virtualPrice']
        else:
            lp_token = Contract(address=lp_token_addr)
            pool_virtual_price = lp_token.functions.get_virtual_price().call()

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


@ Model.describe(slug='curve-fi.all-yield',
                 version='1.4',
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
        all_yields = self.context.run_model(
            slug='compose.map-inputs',
            input={'modelSlug': 'curve-fi.gauge-yield',
                   'modelInputs': gauge_contracts.contracts},
            return_type=MapInputsOutput[Contract, dict])

        res = []
        for pool_n, pool_result in enumerate(all_yields):
            if pool_result.error is not None:
                self.logger.error(pool_result.error)
                raise ModelRunError(pool_result.error.message)
            if pool_result.output is None:
                raise ModelRunError(f'Empty result for {gauge_contracts.contracts[pool_n]}')
            res.append(pool_result)

        return {"results": res}
