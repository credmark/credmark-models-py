# pylint: disable=locally-disabled, line-too-long
from typing import List

import numpy as np
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (
    Account,
    Accounts,
    Address,
    Contract,
    Contracts,
    Maybe,
    Portfolio,
    Position,
    PriceWithQuote,
    Some,
    Token,
    Tokens,
)
from credmark.cmf.types.compose import MapInputsOutput
from credmark.cmf.types.series import BlockSeries
from credmark.dto import DTO, EmptyInputSkipTest
from web3.exceptions import (
    ABIFunctionNotFound,
    BadFunctionCallOutput,
    ContractLogicError,
)

from models.dtos.tvl import TVLInfo
from models.tmp_abi_lookup import CURVE_VYPER_POOL

np.seterr(all='raise')

GAUGE_ABI_LP_TOKEN = '[{"stateMutability":"view","type":"function","name":"lp_token","inputs":[],"outputs":[{"name":"","type":"address"}],"gas":3168}]'  # pylint:disable=line-too-long


# MetaRegistry
# 0xF98B45FA17DE75FB1aD0e7aFD971b0ca00e379fC

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


class CurveFiPoolInfo(CurveFiPoolInfoToken):
    token_prices: List[PriceWithQuote]
    virtualPrice: int
    A: int
    chi: float
    ratio: float
    is_meta: bool
    gauges: Accounts
    gauges_type: List[int]


@Model.describe(slug='curve-fi.get-provider',
                version='1.2',
                display_name='Curve Finance - Get Provider',
                description='Get provider contract',
                category='protocol',
                subcategory='curve',
                output=Contract)
class CurveFinanceGetProvider(Model):
    CURVE_PROVIDER_ALL_NETWORK = '0x0000000022D53366457F9d5E68Ec105046FC4383'

    def run(self, _) -> Contract:
        provider = Contract(address=Address(
            self.CURVE_PROVIDER_ALL_NETWORK).checksum)
        _ = provider.abi
        return provider


@Model.describe(slug='curve-fi.get-registry',
                version='1.2',
                display_name='Curve Finance - Get Registry',
                description='Query provider to get the registry',
                category='protocol',
                subcategory='curve',
                output=Contract)
class CurveFinanceGetRegistry(Model):
    def run(self, _) -> Contract:
        provider = Contract(**self.context.models.curve_fi.get_provider())
        reg_addr = provider.functions.get_registry().call()
        cc = Contract(address=Address(reg_addr).checksum)
        _ = cc.abi
        return cc


@Model.describe(slug="curve-fi.get-gauge-controller",
                version='1.2',
                display_name="Curve Finance - Get Gauge Controller",
                description="Query the registry for the gauge controller",
                category='protocol',
                subcategory='curve',
                output=Contract)
class CurveFinanceGetGauge(Model):
    def run(self, _):
        registry = Contract(**self.context.models.curve_fi.get_registry())
        gauge_addr = registry.functions.gauge_controller().call()
        cc = Contract(address=Address(gauge_addr))
        _ = cc.abi
        return cc


@Model.describe(slug="curve-fi.all-pools",
                version="1.3",
                display_name="Curve Finance - Get all pools",
                description="Query the registry for all pools",
                category='protocol',
                subcategory='curve',
                output=Contracts)
class CurveFinanceAllPools(Model):
    def run(self, _) -> Contracts:
        registry = self.context.run_model('curve-fi.get-registry', {},
                                          return_type=Contract)

        total_pools = registry.functions.pool_count().call()
        pool_contracts = [None] * total_pools
        for i in range(0, total_pools):
            pool_contracts[i] = (Contract(address=registry.functions.pool_list(i).call())
                                 .set_abi(CURVE_VYPER_POOL, set_loaded=True))
            _abi = pool_contracts[i].abi

        return Contracts(contracts=pool_contracts)


class CurvePoolContract(Contract):
    class Config:
        schema_extra = {
            'examples': [{'address': '0x43b4fdfd4ff969587185cdb6f0bd875c5fc83f8c'},
                         {'address': '0xD51a44d3FaE010294C616388b506AcdA1bfAAE46'}]
        }


@Model.describe(slug="curve-fi.pool-info-tokens",
                version="1.14",
                display_name="Curve Finance Pool - Tokens",
                description="The amount of Liquidity for Each Token in a Curve Pool",
                category='protocol',
                subcategory='curve',
                input=CurvePoolContract,
                output=CurveFiPoolInfoToken)
class CurveFinancePoolInfoTokens(Model):
    @staticmethod
    def check_token_address(addrs):
        token_list = Tokens()
        symbols_list = []

        for addr in addrs:
            tok_addr = Address(addr)
            if not tok_addr.is_null():
                tok = Token(address=tok_addr.checksum).as_erc20(
                    set_loaded=True)
                symbols_list.append(tok.symbol)
                token_list.append(tok)
        return token_list, symbols_list

    def run(self, input: CurvePoolContract) -> CurveFiPoolInfoToken:
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
                _ = input.abi
            except ModelDataError:
                input = CurvePoolContract(address=input.address).set_abi(CURVE_VYPER_POOL, set_loaded=True)

            if input.abi is not None and 'minter' in input.abi.functions:
                minter_addr = input.functions.minter().call()
                return self.context.run_model(
                    self.slug,
                    input=Contract(address=Address(minter_addr)),
                    return_type=CurveFiPoolInfoToken)
            try:
                pool_addr = (registry.functions
                             .get_pool_from_lp_token(input.address.checksum).call())
                if not Address(pool_addr).is_null():
                    return self.context.run_model(self.slug,
                                                  input=Contract(address=Address(pool_addr)),
                                                  return_type=CurveFiPoolInfoToken)
            except Exception:
                pass

            tokens = Tokens()
            tokens_symbol = []
            underlying = Tokens()
            underlying_symbol = []
            for i in range(8):
                try:
                    tok_addr = Address(input.functions.coins(i).call())
                    if tok_addr.is_null():
                        break
                    token = Token(address=tok_addr)
                    tokens.append(token)
                    tokens_symbol.append(token.symbol)
                    balances.append(token.scaled(
                        input.functions.balances(i).call()))
                    try:
                        und = input.functions.underlying_coins(i).call()
                        underlying.append(und)
                        underlying_symbol.append(und.symbol)
                    except (ABIFunctionNotFound, ContractLogicError):
                        pass
                except ContractLogicError:
                    break

        balances_token = [t.balance_of_scaled(
            input.address.checksum) for t in tokens]

        admin_fees = [bal_token-bal
                      for bal, bal_token in zip(balances, balances_token)]

        try:
            name = input.functions.name().call()
        except Exception:
            name = ""

        lp_token_addr = Address.null()
        lp_token_name = ''
        try:
            lp_token_addr = Address(
                registry.functions.get_lp_token(input.address).call())
        except ABIFunctionNotFound:
            try:
                lp_token_addr = Address(input.functions.lp_token().call())
            except ABIFunctionNotFound:
                try:
                    provider = self.context.run_model(
                        'curve-fi.get-provider', {}, return_type=Contract)
                    pool_info_addr = Address(provider.functions.get_address(1).call())
                    pool_info_contract = Contract(address=pool_info_addr.checksum)
                    pool_info = (pool_info_contract.functions.get_pool_info(input.address.checksum).call())
                    lp_token_addr = Address(pool_info[5])
                except ContractLogicError:
                    pass

        if not lp_token_addr.is_null():
            lp_token = Token(address=lp_token_addr.checksum)
            lp_token_name = lp_token.name
        else:
            if input.abi is not None and 'token' in input.abi.functions:
                lp_token_addr = Address(input.functions.token().call())
                lp_token = Token(address=lp_token_addr.checksum)
                lp_token_name = lp_token.name
            else:
                lp_token = Token(address=input.address)
                try:
                    _ = lp_token.abi
                except ModelDataError:
                    lp_token = lp_token.as_erc20(set_loaded=True)
                lp_token_name = lp_token.name
                lp_token_addr = lp_token.address

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
                                    lp_token_addr=lp_token_addr
                                    )


@Model.describe(slug="curve-fi.pool-info",
                version="1.30",
                display_name="Curve Finance Pool Liquidity",
                description="The amount of Liquidity for Each Token in a Curve Pool",
                category='protocol',
                subcategory='curve',
                input=CurvePoolContract,
                output=CurveFiPoolInfo)
class CurveFinancePoolInfo(Model):
    def run(self, input: CurvePoolContract) -> CurveFiPoolInfo:
        registry = Contract(**self.context.models.curve_fi.get_registry())
        pool_info = self.context.run_model('curve-fi.pool-info-tokens',
                                           input,
                                           return_type=CurveFiPoolInfoToken)

        pool_contract = Contract(address=pool_info.address)

        def _use_for() -> List[PriceWithQuote]:
            token_prices = []
            for tok in pool_info.tokens:
                token_price = self.context.run_model(
                    'price.dex-maybe',
                    {'base': tok},
                    return_type=Maybe[PriceWithQuote])
                token_prices.append(token_price.get_just(PriceWithQuote.usd()))
            return token_prices

        token_prices = _use_for()

        np_balance = np.array(pool_info.balances_token) * np.array([p.price for p in token_prices])
        n_asset = np_balance.shape[0]
        product_balance = np_balance.prod()
        avg_balance = np_balance.mean()

        # Calculating ratio, this gives information about peg
        ratio = product_balance / np.power(avg_balance, n_asset)

        try:
            virtual_price = pool_contract.functions.get_virtual_price().call()
        except Exception:
            virtual_price = 10**18

        try:
            pool_A = pool_contract.functions.A().call()
        except Exception:
            pool_A = 0

        # Calculating 'chi'
        chi = pool_A * ratio

        gauges, gauges_type = registry.functions.get_gauges(
            input.address.checksum).call()
        gauges = [Account(address=g)
                  for g in gauges if not Address(g).is_null()]
        gauges_type = gauges_type[:len(gauges)]

        if len(gauges) == 0:
            gauges = self.context.run_model(
                'curve-fi.all-gauges', {}, return_type=CurveFiAllGaugesOutput)

            gauges = [Account(address=g.address)
                      for g, lp in zip(gauges, gauges.lp_tokens)
                      if lp.address == pool_info.lp_token_addr]
            gauges_type = [0] * len(gauges)

        is_meta = registry.functions.is_meta(
            pool_contract.address.checksum).call()

        return CurveFiPoolInfo(**(pool_info.dict()),
                               token_prices=token_prices,
                               virtualPrice=virtual_price,
                               A=pool_A,
                               ratio=ratio,
                               chi=chi,
                               is_meta=is_meta,
                               gauges=Accounts(accounts=gauges),
                               gauges_type=gauges_type)


@Model.describe(slug="curve-fi.pool-tvl",
                version="1.9",
                display_name="Curve Finance Pool - TVL",
                description="Total amount of TVL",
                category='protocol',
                subcategory='curve',
                input=CurvePoolContract,
                output=TVLInfo)
class CurveFinancePoolTVL(Model):
    def run(self, input: CurvePoolContract) -> TVLInfo:
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

        pool_name = pool_info.lp_token_name

        tvl_info = TVLInfo(
            address=input.address,
            name=pool_name,
            portfolio=Portfolio(positions=positions),
            tokens_symbol=pool_info.tokens_symbol,
            prices=pool_info.token_prices,
            tvl=tvl)

        return tvl_info


@Model.describe(slug="curve-fi.all-pools-info",
                version="2.2",
                display_name="Curve Finance Pool Liquidity - All",
                description="The amount of Liquidity for Each Token in a Curve Pool - All",
                category='protocol',
                subcategory='curve',
                output=Some[CurveFiPoolInfo])
class CurveFinanceTotalTokenLiquidity(Model):
    def run(self, _) -> Some[CurveFiPoolInfo]:
        pool_contracts = self.context.run_model(
            'curve-fi.all-pools', {}, return_type=Contracts)

        def _use_for():
            pool_infos = []
            for pool in pool_contracts:
                pool_info = self.context.run_model(
                    'curve-fi.pool-info',
                    pool,
                    return_type=CurveFiPoolInfo)
                pool_infos.append(pool_info)
            return pool_infos

        def _use_compose():
            model_slug = 'curve-fi.pool-info'
            all_pools = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': model_slug,
                       'modelInputs': pool_contracts.contracts},
                return_type=MapInputsOutput[Contract, CurveFiPoolInfo])

            pool_infos = []
            errors = []
            for pool_n, pool_result in enumerate(all_pools):
                if pool_result.error is not None:
                    errors.append((pool_n, pool_result.error))
                else:
                    pool_infos.append(pool_result.output)

            if len(errors) > 0:
                for error_n, (pool_n, err) in enumerate(errors):
                    self.logger.error(
                        (f'{error_n+1}/{len(errors)}: ' +
                         f'Error with models({self.context.block_number}).' +
                         f'{model_slug.replace("-","_")}({pool_contracts.contracts[pool_n]})'))
                    self.logger.error(err)
                raise ModelRunError(
                    errors[0][1].message + f' For {pool_infos[errors[0][0]]=}')

            return pool_infos

        pool_infos = _use_compose()

        all_pools_info = Some[CurveFiPoolInfo](some=pool_infos)

        # (pd.DataFrame((all_pools_info.dict())['some'])
        # .to_csv(f'tmp/curve-all-info_{self.context.block_number}.csv'))
        return all_pools_info


class CurveFiAllGaugesOutput(Contracts):
    lp_tokens: Accounts


@Model.describe(slug="curve-fi.all-gauges",
                version='1.4',
                display_name="Curve Finance Gauge List",
                description="All Gauge Contracts for Curve Finance Pools",
                category='protocol',
                subcategory='curve',
                output=CurveFiAllGaugesOutput)
class CurveFinanceAllGauges(Model):
    def run(self, _) -> CurveFiAllGaugesOutput:
        gauge_controller = Contract(**self.context.models.curve_fi.get_gauge_controller())
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
                gauge_contract = Contract(gauge_contract.address).set_abi(
                    GAUGE_ABI_LP_TOKEN, set_loaded=True)
            try:
                lp_token_addr = gauge_contract.functions.lp_token().call()
                lp_tokens.append(Account(address=lp_token_addr))
            except (BadFunctionCallOutput, ABIFunctionNotFound, ContractLogicError):
                lp_tokens.append(Account(address=Address.null()))
        return CurveFiAllGaugesOutput(contracts=gauges,
                                      lp_tokens=Accounts(accounts=lp_tokens))


class CurveGaugeContract(Contract):
    class Config:
        schema_extra = {
            'examples': [{'address': '0x824F13f1a2F29cFEEa81154b46C0fc820677A637'},
                         {'address': '0x72E158d38dbd50A483501c24f792bDAAA3e7D55C'},
                         {'address': '0x11137B10C210b579405c21A07489e28F3c040AB1'},
                         {'address': '0xbFcF63294aD7105dEa65aA58F8AE5BE2D9d0952A'}]
        }


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
                input=CurvePoolContract,
                output=dict)
class CurveFinanceHistoricalLPDist(Model):
    def run(self, input: CurvePoolContract) -> dict:
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
                version='1.5',
                category='protocol',
                subcategory='curve',
                input=CurveGaugeContract,
                output=dict)
class CurveFinanceAverageGaugeYield(Model):
    CRV_PRICE = 3.0

    def run(self, input: CurveGaugeContract) -> dict:
        """
        presuming that crv has a constant value of $3
        """

        lp_token_addr = input.functions.lp_token().call()

        registry = self.context.run_model(
            'curve-fi.get-registry', {}, return_type=Contract)
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
                            yields.append((new_portfolio_value - old_portfolio_value) / old_portfolio_value)
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
