# pylint: disable=locally-disabled, unused-import

import pandas as pd
import numpy as np
from typing import List, Union
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
    Portfolio,
    Position,
    Price,
)

from models.dtos.tvl import TVLInfo
from models.dtos.volume import (
    TradingVolume,
    TokenTradingVolume,
    VolumeInput,
)

from web3.exceptions import ABIFunctionNotFound, ContractLogicError


@Model.describe(slug='curve-fi.get-provider',
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


@Model.describe(slug='curve-fi.get-registry',
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


@Model.describe(slug="curve-fi.get-gauge-controller",
                version='1.2',
                display_name="Curve Finance - Get Gauge Controller",
                description="Query the registry for the guage controller")
class CurveFinanceGetGauge(Model):
    def run(self, input):
        registry = Contract(**self.context.models.curve_fi.get_registry())
        gauge_addr = registry.functions.gauge_controller().call()
        return Contract(address=Address(gauge_addr).checksum)


@Model.describe(slug="curve-fi.all-pools",
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


class CurveFiPoolInfo(Contract):
    virtualPrice: int
    tokens: Tokens
    tokens_symbol: List[str]
    balances: List[float]  # exclude fee
    balances_token: List[float]  # include fee
    admin_fees: List[float]
    underlying_tokens: Tokens
    underlying_tokens_symbol: List[str]
    A: int
    is_meta: bool
    name: str
    lp_token_name: str
    lp_token_addr: Address
    pool_token_name: str
    pool_token_addr: Address


class CurveFiPoolInfos(DTO):
    pool_infos: List[CurveFiPoolInfo]


@Model.describe(slug="curve-fi.pool-info",
                version="1.7",
                display_name="Curve Finance Pool Liqudity",
                description="The amount of Liquidity for Each Token in a Curve Pool",
                input=Contract,
                output=CurveFiPoolInfo)
class CurveFinancePoolInfo(Model):
    def check_token_address(self, addrs):
        token_list = Tokens()
        symbols_list = []

        for addr in addrs:
            tok_addr = Address(addr)
            if tok_addr != Address.null():
                tok = Token(address=tok_addr.checksum)
                if tok.address == '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee':
                    symbols_list.append('ETH')
                else:
                    symbols_list.append(tok.symbol)
                token_list.append(tok)
        return token_list, symbols_list

    def run(self, input: Contract) -> CurveFiPoolInfo:
        registry = Contract(**self.context.models.curve_fi.get_registry())

        balances = []

        # The default is to use registry
        use_registry = True

        # Equivalent to input.functions.balances(ii).call()
        try:
            balances_tokens = registry.functions.get_balances(input.address.checksum).call()
        except ContractLogicError:
            try:
                minter_addr = input.functions.minter().call()
                return self.context.run_model(self.slug,
                                              input=Contract(address=Address(minter_addr)),
                                              return_type=CurveFiPoolInfo)
            except ABIFunctionNotFound:
                pass

            balances_tokens = []
            use_registry = False

        if use_registry:
            # Equivalent to input.functions.coins(ii).call()
            coins = registry.functions.get_coins(input.address.checksum).call()
            tokens, tokens_symbol = self.check_token_address(coins)

            # However, input.functions.underlying_coins(ii).call() is empty for some pools
            underlying_coins = (registry.functions.get_underlying_coins(input.address.checksum)
                                .call())
            underlying, underlying_symbol = self.check_token_address(underlying_coins)
            balances_raw = balances_tokens[:len(tokens_symbol)]

            balances = [
                t.scaled(bal)
                if t.address != '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
                else float(self.context.web3.fromWei(bal, 'ether'))
                for bal, t in zip(balances_raw, tokens)
            ]
        else:
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

        balances_token = [
            t.scaled(t.functions.balanceOf(input.address).call())
            if t.address != '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
            else float(self.context.web3.fromWei(self.context.web3.eth.get_balance(input.address),
                                                 'ether'))
            for t in tokens]
        admin_fees = [bal_token-bal for bal, bal_token in zip(balances, balances_token)]

        try:
            a = input.functions.A().call()
            virtual_price = input.functions.get_virtual_price().call()
        except Exception as _err:
            virtual_price = (10**18)
            a = 0

        is_meta = registry.functions.is_meta(input.address.checksum).call()

        try:
            name = input.functions.name().call()
        except Exception as _err:
            name = ""

        lp_token_addr = Address.null()
        lp_token_name = ''
        try:
            lp_token_addr = Address(input.functions.lp_token().call())
            lp_token = Token(address=lp_token_addr.checksum)
            lp_token_name = lp_token.name
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
                lp_token = Token(address=lp_token_addr.checksum)
                lp_token_name = lp_token.name
            except ContractLogicError:
                pass

        pool_token_addr = Address.null()
        pool_token_name = ''
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
                               balances_token=balances_token,
                               admin_fees=admin_fees,
                               underlying_tokens=underlying,
                               underlying_tokens_symbol=underlying_symbol,
                               A=a,
                               is_meta=is_meta,
                               name=name,
                               lp_token_name=lp_token_name,
                               lp_token_addr=lp_token_addr,
                               pool_token_name=pool_token_name,
                               pool_token_addr=pool_token_addr,
                               )


# TODO: Temporary price model for stablecoins on Curve
@Model.describe(slug="curve-fi.price",
                version="1.1",
                display_name="Curve Finance Pool - Price for stablecoins",
                description="For those stablecoins primarily traded in curve",
                input=Token,
                output=Price)
class CurveFinancePrice(Model):
    """
    Price from Curve Pool.
    For there are three types
    - Stablecoins: list of tokens hard-coded to $1 now. TODO
    - Derived: From pool with other tokens with prices from oracle
    - LP token: From the minimal price of the token in the pool * virtual price

    Reference for LP token:
    - Chainlink: https://blog.chain.link/using-chainlink-oracles-to-securely-utilize-curve-lp-pools/
    """
    CRV_STABLECOINS = {
        1: {
            'cyDAI': Address('0x8e595470ed749b85c6f7669de83eae304c2ec68f'),
            'cyUSDC': Address('0x76eb2fe28b36b3ee97f3adae0c69606eedb2a37c'),
            'cyUSDT': Address('0x48759f220ed983db51fa7a8c0d2aab8f3ce4166a'),
        }
    }

    CRV_DERIVED = {
        1: {
            Address('0xFEEf77d3f69374f66429C91d732A244f074bdf74'):
            {
                'name': 'cvxFXS',
                'pool_address': '0xd658A338613198204DCa1143Ac3F01A722b5d94A'
            },
        }
    }

    CRV_LP = {
        1: {
            Address('0x6c3f90f043a72fa612cbac8115ee7e52bde6e490'):
            {
                'name': '3Crv',
                'pool_address': '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7',
            }
        }
    }

    @staticmethod
    def supported_coins(chain_id):
        return (list(CurveFinancePrice.CRV_STABLECOINS[chain_id].values()) +
                list(CurveFinancePrice.CRV_DERIVED[chain_id].keys()) +
                list(CurveFinancePrice.CRV_LP[chain_id].keys())
                )

    def run(self, input: Token) -> Price:
        if input.address in self.CRV_STABLECOINS[self.context.chain_id].values():
            return Price(price=1.0, src=self.slug)

        derived_info = self.CRV_DERIVED[self.context.chain_id].get(input.address)
        if derived_info is not None:
            pool = Contract(address=derived_info['pool_address'])
            pool_info = self.context.run_model('curve-fi.pool-info',
                                               input=pool,
                                               return_type=CurveFiPoolInfo)
            n_token_input = np.where([tok == input for tok in pool_info.tokens])[0].tolist()
            if len(n_token_input) != 1:
                raise ModelRunError(
                    f'{self.slug} does not find {input=} in pool {pool.address=}')
            n_token_input = n_token_input[0]

            price_to_others = []
            for n_token_other, other_token in enumerate(pool_info.tokens):
                if n_token_other != n_token_input:
                    ratio_to_other = pool.functions.get_dy(n_token_input,
                                                           n_token_other,
                                                           10**input.decimals).call() / 1e18
                    price_other = self.context.run_model('chainlink.price-usd',
                                                         input=other_token,
                                                         return_type=Price).price
                    price_to_others.append(ratio_to_other * price_other)

            n_price_min = np.where(price_to_others)[0][0]
            return Price(price=np.min(price_to_others),
                         src=f'{self.slug}|{pool.address}|{pool_info.tokens_symbol[n_price_min]}')

        lp_token_info = self.CRV_LP[self.context.chain_id].get(input.address)
        if lp_token_info is not None:
            pool = Contract(address=lp_token_info['pool_address'])
            pool_info = self.context.run_model('curve-fi.pool-info',
                                               input=pool,
                                               return_type=CurveFiPoolInfo)
            if pool_info.lp_token_addr != input.address:
                raise ModelRunError(
                    f'{self.slug} does not find LP {input=} in pool {pool.address=}')

            price_tokens = []
            for tok in pool_info.tokens:
                price_tok = self.context.run_model('chainlink.price-usd',
                                                   input=tok,
                                                   return_type=Price).price
                price_tokens.append(price_tok)

            virtual_price = pool.functions.get_virtual_price().call()
            lp_token_price = input.scaled(min(price_tokens) * virtual_price)
            n_min_token_symbol = np.where(np.isclose(min(price_tokens), price_tokens))[0][0]
            min_token_symbol = pool_info.tokens_symbol[n_min_token_symbol]

            return Price(price=lp_token_price,
                         src=(f'{self.slug}|{pool.address}|LP|'
                              f'{min_token_symbol}|min({",".join(pool_info.tokens_symbol)})'))

        raise ModelRunError(f'{self.slug} does not support {input=}')


@ Model.describe(slug="curve-fi.pool-tvl",
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
        prices = []
        tvl = 0.0
        for tok, bal in zip(pool_info.tokens.tokens, pool_info.balances):
            positions.append(Position(amount=bal, asset=tok))

            if tok.address in CurveFinancePrice.supported_coins(self.context.chain_id):
                tok_price = self.context.run_model('curve-fi.price',
                                                   input=tok,
                                                   return_type=Price)
            else:
                tok_price = self.context.run_model('chainlink.price-usd',
                                                   input=tok,
                                                   return_type=Price)
            prices.append(tok_price)
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
            prices=prices,
            tvl=tvl
        )

        return tvl_info


class HistoricalRunModelInput(DTO):
    model_slug: str
    model_input: dict
    window: str
    interval: str


# TODO: Pre-composer model
@ Model.describe(slug="historical.run-model",
                 version="1.0",
                 display_name="Run Any model for historical",
                 description="",
                 input=HistoricalRunModelInput,
                 output=dict)
class HistoricalRunModel(Model):
    def run(self, input: HistoricalRunModelInput) -> dict:
        window = input.window
        interval = input.interval

        result = self.context.historical.run_model_historical(
            model_slug=input.model_slug,
            model_input=input.model_input,
            window=window,
            interval=interval,
            end_timestamp=self.context.block_number.timestamp)

        return {'result': result}


@ Model.describe(slug="curve-fi.all-pools-info",
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
                 version='1.2',
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
