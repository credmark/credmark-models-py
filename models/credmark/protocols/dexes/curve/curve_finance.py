# pylint: disable=locally-disabled, line-too-long
import math
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
    Network,
    Portfolio,
    Position,
    PriceWithQuote,
    Some,
    Token,
    Tokens,
)
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import EmptyInputSkipTest
from web3.exceptions import (
    ABIFunctionNotFound,
    ContractLogicError,
)

from models.credmark.protocols.dexes.curve.curve_meta import (
    CurveGauges,
    CurveMeta,
    CurvePool,
    CurvePoolMeta,
    CurvePoolMetas,
    CurvePoolPosition,
    CurvePoolPositions,
    CurvePoolType,
)
from models.dtos.tvl import TVLInfo

np.seterr(all='raise')


class CurvePoolInfoToken(CurvePool):
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


class CurvePoolInfo(CurvePoolInfoToken):
    token_prices: List[PriceWithQuote]
    virtualPrice: int
    A: int
    chi: float
    ratio: float
    is_meta: bool
    gauges: Accounts


@Model.describe(slug='curve-fi.get-provider',
                version='1.4',
                display_name='Curve Finance - Get Provider',
                description='Get provider contract',
                category='protocol',
                subcategory='curve',
                output=Contract)
class CurveFinanceGetProvider(Model, CurveMeta):
    def run(self, _) -> Contract:
        return self.get_provider()


@Model.describe(slug='curve-fi.get-registry',
                version='1.4',
                display_name='Curve Finance - Get Registry',
                description='Query provider to get the registry',
                category='protocol',
                subcategory='curve',
                output=Contract)
class CurveFinanceGetRegistry(Model, CurveMeta):
    def run(self, _) -> Contract:
        return self.get_registry()


@Model.describe(slug="curve-fi.get-gauge-controller",
                version='1.4',
                display_name="Curve Finance - Get Gauge Controller",
                description="Query the registry for the gauge controller",
                category='protocol',
                subcategory='curve',
                output=Contract)
class CurveFinanceGetGauge(Model, CurveMeta):
    def run(self, _):
        return self.get_gauge_controller()


@Model.describe(slug="curve-fi.all-pools",
                version="1.11",
                display_name="Curve Finance - Get all pools",
                description="Query the registry for all pools",
                category='protocol',
                subcategory='curve',
                output=CurvePoolMetas)
class CurveFinanceAllPools(Model, CurveMeta):
    def add_pools_from_stableswap(self, registry, permissionless, registry_type, all_gauges_dict, out_all_addrs, out_pool_contracts):
        original_length = len(out_pool_contracts)
        m = self.context.multicall
        total_pools = registry.functions.pool_count().call()
        res_addr = m.try_aggregate_unwrap(
            [registry.functions.pool_list(i) for i in range(total_pools)])
        res_is_meta = m.try_aggregate_unwrap(
            [registry.functions.is_meta(res) for res in res_addr])
        if permissionless:
            # Factory: Use Pool / LP token to get gauge
            res_lp_token = res_addr
        else:
            # Registry: Use LP token to get gauge
            res_lp_token = m.try_aggregate_unwrap(
                [registry.functions.get_lp_token(addr) for addr in res_addr])
        assert all(not Address(x).is_null() for x in res_lp_token)

        duplicated = 0
        for pool_address, is_meta, lp_token in zip(res_addr, res_is_meta, res_lp_token):
            if pool_address in out_all_addrs:
                self.logger.warning(
                    f"Duplicate pool address {pool_address}/{is_meta} in {registry_type}")
                duplicated += 1
                continue

            gauge_addr = all_gauges_dict.get(lp_token)
            if gauge_addr:
                gauge = Token(address=gauge_addr)
            else:
                gauge = None

            if is_meta:
                out_pool_contracts.append(CurvePoolMeta(
                    address=pool_address,
                    pool_type=CurvePoolType.MetaPool,
                    gauge=gauge,
                    lp_token=Token(address=lp_token)))
            else:
                out_pool_contracts.append(CurvePoolMeta(
                    address=pool_address,
                    pool_type=CurvePoolType.StableSwap,
                    gauge=gauge,
                    lp_token=Token(address=lp_token)))
            if pool_address in out_all_addrs:
                raise ModelDataError(f"Duplicate pool address {pool_address}")
            out_all_addrs.add(pool_address)
        self.logger.info(
            f'{original_length}+{total_pools}-{duplicated}={len(out_all_addrs)} from {registry_type}')

    def add_pools_from_cryptoswap(self, factory, permissionless, factory_type, use_pool_as_lp, all_gauges_dict, pool_type, out_all_addrs, out_pool_contracts):
        original_length = len(out_pool_contracts)
        m = self.context.multicall
        total_pools = factory.functions.pool_count().call()
        duplicated = 0
        res_addr = m.try_aggregate_unwrap(
            [factory.functions.pool_list(i) for i in range(total_pools)])
        if permissionless:
            if use_pool_as_lp:
                res_lp_token = res_addr
            else:
                # Factory: Use Pool / LP token to get gauge
                res_lp_token = m.try_aggregate_unwrap(
                    [factory.functions.get_token(addr) for addr in res_addr])
        else:
            # Registry: Use LP token to get gauge
            res_lp_token = m.try_aggregate_unwrap(
                [factory.functions.get_lp_token(addr) for addr in res_addr])

        for pool_address, lp_token in zip(res_addr, res_lp_token):
            if pool_address in out_all_addrs:
                self.logger.warning(
                    f"Duplicate pool address {pool_address} in {factory_type}")
                duplicated += 1
                continue

            gauge_addr = all_gauges_dict.get(lp_token)
            gauge = None
            if gauge_addr:
                gauge = Token(address=gauge_addr)
            out_pool_contracts.append(CurvePoolMeta(
                address=pool_address,
                pool_type=pool_type,
                gauge=gauge,
                lp_token=Token(address=lp_token)))
            out_all_addrs.add(pool_address)
        self.logger.info(
            f'{original_length}+{total_pools}-{duplicated}={len(out_all_addrs)} from {factory_type}')
        return res_addr

    # pylint: disable=too-many-branches
    def run(self, _) -> CurvePoolMetas:
        '''
        # Curve deployer on mainnet
        0x90e00ace148ca3b23ac1bc8c240c2a7dd9c2d7f5
        0xb9fc157394af804a3578134a6585c0dc9cc990d4
        0x8f942c20d02befc377d41445793068908e2250d0
        0xf18056bbd320e96a48e3fbf8bc061322531aac99

        # APE deployer on mainnet (not included in main curve)
        0xfD6f33A0509ec67dEFc500755322aBd9Df1bD5B8

        # meta_registry on mainnet
        # https://etherscan.io/address/0xf98b45fa17de75fb1ad0e7afd971b0ca00e379fc#readContract

        sub-registry under meta_registry
        0: https://etherscan.io/address/0x46a8a9CF4Fc8e99EC3A14558ACABC1D93A27de68: 49
        1: https://etherscan.io/address/0x127db66E7F0b16470Bec194d0f496F9Fa065d0A9: 366
        2: https://etherscan.io/address/0x5f493fEE8D67D3AE3bA730827B34126CFcA0ae94: 9
        3: https://etherscan.io/address/0xC4F389020002396143B863F6325aA6ae481D19CE: 306
        4: https://etherscan.io/address/0x538E984C2d5f821d51932dd9C570Dff192D3DF2D: 17
        5: https://etherscan.io/address/0x30a4249C42be05215b6063691949710592859697: 5
        49 + 366 +_9 + 306 + 17 + 5
        '''

        all_gauges = self.context.run_model('curve-fi.all-gauges', {}, return_type=CurveGauges)
        all_gauges_dict = {g.lp_token.address.checksum: g.address.checksum
                           for g in all_gauges.contracts}
        # [g for g in all_gauges if g.lp_token.address == '0x7f90122bf0700f9e7e1f688fe926940e8839f353']

        all_addrs = set()
        pool_contracts = []

        registry = self.get_registry()
        if not registry.address.is_null():
            self.add_pools_from_stableswap(registry, False, 'registry',
                                           all_gauges_dict, all_addrs, pool_contracts)
        del registry

        metapool_factory = self.get_metapool_factory()
        if not metapool_factory.address.is_null():
            self.add_pools_from_stableswap(metapool_factory, True, 'metapool factory',
                                           all_gauges_dict, all_addrs, pool_contracts)
        del metapool_factory

        cryptoswap_registry = self.get_cryptoswap_registry()
        if not cryptoswap_registry.address.is_null():
            self.add_pools_from_cryptoswap(cryptoswap_registry, False, 'cryptoswap registry', False,
                                           all_gauges_dict, CurvePoolType.CryptoSwap, all_addrs, pool_contracts)
        del cryptoswap_registry

        # Address('0x2889302a794da87fbf1d6db415c1492194663d13').checksum in res_addr
        cryptoswap_factory = self.get_cryptoswap_factory()
        if not cryptoswap_factory.address.is_null():
            if self.context.network == Network.Optimism:
                #  There is no get_lp_token/get_token on Optimism factory
                self.add_pools_from_cryptoswap(cryptoswap_factory, True, 'cryptoswap factory', True,
                                               all_gauges_dict, CurvePoolType.CryptoSwapFactory, all_addrs, pool_contracts)
            else:
                self.add_pools_from_cryptoswap(cryptoswap_factory, True, 'cryptoswap factory', False,
                                               all_gauges_dict, CurvePoolType.CryptoSwapFactory, all_addrs, pool_contracts)
        del cryptoswap_factory

        if self.context.network in [Network.ArbitrumOne, Network.Mainnet]:
            tricrypto_ng_factory = self.get_tricrypto_ng_factory(self.context.network)
            self.add_pools_from_cryptoswap(tricrypto_ng_factory, True, 'tricrypto-ng factory', True,
                                           all_gauges_dict, CurvePoolType.CryptoSwapFactory, all_addrs, pool_contracts)

        if self.context.network in [Network.Mainnet]:
            crvusd_factory = self.get_crvusd_factory(self.context.network)
            self.add_pools_from_stableswap(crvusd_factory, True, 'crvusd factory',
                                           all_gauges_dict, all_addrs, pool_contracts)

        self.logger.info(
            f'{len(all_gauges.contracts)}/{len(all_gauges_dict)} gauges, found {len([p for p in pool_contracts if p.gauge])} in pools')

        g_addr = set(x.address for x in all_gauges.contracts)
        g_addr_in_pools = set(g.gauge.address for g in pool_contracts if g.gauge)
        g_not_in_pools = g_addr - g_addr_in_pools
        self.logger.info(
            f'Outstanding gauges [{len(g_addr)-len(g_addr_in_pools)}]: {g_not_in_pools}')

        # [g for g in pool_contracts if g.address == '0x6eb2dc694eb516b16dc9fbc678c60052bbdd7d80']
        # [g for g in all_gauges if g.lp_token.address == '0xdbcd16e622c95acb2650b38ec799f76bfc557a0b']
        # !list(x for x in all_gauges.contracts if x.address in ['0x02246583870b36be0fef2819e1d3a771d6c07546'])
        # !list(x for x in pool_contracts if x.lp_token.address in ['0x137469b55d1f15651ba46a89d0588e97dd0b6562'])

        self.logger.info(f'{len(pool_contracts)} pools on chain {self.context.network}')
        return CurvePoolMetas(contracts=pool_contracts)


@Model.describe(slug="curve-fi.account",
                version="0.1",
                display_name="Curve Finance Pool - Account",
                description="The amount of user's liquidity in a Curve Pool / Gauge",
                category='protocol',
                subcategory='curve',
                input=Account,
                output=CurvePoolPositions)
class CurveFinanceAccount(Model, CurveMeta):
    def run(self, input: Account) -> CurvePoolPositions:
        all_pools = self.context.run_model('curve-fi.all-pools', {}, return_type=CurvePoolMetas)
        lp_calls = []
        lp_scale_calls = []
        gauge_calls = []
        gauge_scale_calls = []
        gauge_skips = []
        for n_pool, pool in enumerate(all_pools):
            lp_token = pool.get_lp_token()
            gauge = pool.get_gauge()
            lp_calls.append(lp_token.functions.balanceOf(input.address.checksum))
            lp_scale_calls.append(lp_token.functions.decimals())

            if gauge:
                gauge_calls.append(gauge.functions.balanceOf(input.address.checksum))
                gauge_scale_calls.append(gauge.functions.decimals())
                # if len(gauge_calls) == 8:
                #    breakpoint()
            else:
                gauge_skips.append(n_pool)

        m = self.context.multicall
        res_lp_call = m.try_aggregate_unwrap(lp_calls)
        res_lp_scale_call = m.try_aggregate_unwrap(lp_scale_calls)
        res_gauge_call = m.try_aggregate_unwrap(gauge_calls)
        res_gauge_scale_call = m.try_aggregate_unwrap(gauge_scale_calls, replace_with=18)

        for s in gauge_skips:
            res_gauge_call.insert(s, None)
            res_gauge_scale_call.insert(s, None)

        assert len(res_gauge_call) == len(all_pools.contracts)

        positions = []
        for pool, lp_bal, lp_scale, gauge_bal, gauge_scale in zip(all_pools, res_lp_call, res_lp_scale_call, res_gauge_call, res_gauge_scale_call):
            if lp_bal > 0 or (gauge_bal and gauge_bal > 0):
                positions.append(CurvePoolPosition(**pool.dict(),
                                                   lp_balance=lp_bal / 10**lp_scale,
                                                   gauge_balance=gauge_bal / 10**gauge_scale if gauge_bal else None))
        return CurvePoolPositions(positions=positions)


@Model.describe(slug="curve-fi.pool-info-tokens",
                version="1.18",
                display_name="Curve Finance Pool - Tokens",
                description="The amount of Liquidity for Each Token in a Curve Pool",
                category='protocol',
                subcategory='curve',
                input=CurvePool,
                output=CurvePoolInfoToken)
class CurveFinancePoolInfoTokens(Model, CurveMeta):
    @staticmethod
    def check_token_address(addrs):
        token_list = Tokens()
        symbols_list = []

        for addr in addrs:
            tok_addr = Address(addr)
            if not tok_addr.is_null():
                tok = (Token(address=tok_addr.checksum)
                       .as_erc20(set_loaded=True))
                if tok_addr.checksum == '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE':
                    symbols_list.append('ETH')
                else:
                    symbols_list.append(tok.symbol)
                token_list.append(tok)
        return token_list, symbols_list

    def run(self, input: CurvePool) -> CurvePoolInfoToken:
        input = input.get_pool()
        registry = self.get_registry()
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
                input = CurvePool(address=input.address, pool_type=None).get_pool()

            if input.abi is not None and 'minter' in input.abi.functions:
                minter_addr = input.functions.minter().call()
                return self.context.run_model(
                    self.slug,
                    input=Contract(address=Address(minter_addr)),
                    return_type=CurvePoolInfoToken)
            try:
                pool_addr = (registry.functions
                             .get_pool_from_lp_token(input.address.checksum).call())
                if not Address(pool_addr).is_null():
                    return self.context.run_model(self.slug,
                                                  input=Contract(address=Address(pool_addr)),
                                                  return_type=CurvePoolInfoToken)
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

        balances_token = [t.balance_of_scaled(input.address.checksum)
                          for t in tokens]

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
                    pool_info_contract = self.get_pool_info()
                    pool_info = (pool_info_contract.functions
                                 .get_pool_info(input.address.checksum).call())
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

        return CurvePoolInfoToken(**(input.dict()),
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
                version="1.34",
                display_name="Curve Finance Pool Liquidity",
                description="The amount of Liquidity for Each Token in a Curve Pool",
                category='protocol',
                subcategory='curve',
                input=CurvePool,
                output=CurvePoolInfo)
class CurveFinancePoolInfo(Model, CurveMeta):
    def run(self, input: CurvePool) -> CurvePoolInfo:
        registry = self.get_registry()
        pool_info = self.context.run_model('curve-fi.pool-info-tokens',
                                           input,
                                           return_type=CurvePoolInfoToken)
        pool_contract = pool_info.get_pool()

        def _use_for() -> List[PriceWithQuote]:
            token_prices = []
            for tok in pool_info.tokens:
                token_price = self.context.run_model(
                    'price.dex-maybe',
                    {'base': tok},
                    return_type=Maybe[PriceWithQuote])
                token_prices.append(token_price.get_just(PriceWithQuote.usd()))
            return token_prices

        if self.context.network == Network.Mainnet:
            token_prices = _use_for()
        else:
            token_prices = [PriceWithQuote.usd() for _ in pool_info.tokens]

        np_balance = np.array(pool_info.balances_token) * np.array([p.price for p in token_prices])
        n_asset = np_balance.shape[0]
        product_balance = np_balance.prod()
        avg_balance = np_balance.mean()

        # Calculating ratio, this gives information about peg
        if math.isclose(avg_balance, 0):
            ratio = 0
        else:
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

        gauges, _gauges_type = (registry.functions
                                .get_gauges(input.address.checksum).call())
        gauges = [Account(address=g)
                  for g in gauges if not Address(g).is_null()]

        if self.context.network == Network.Mainnet:
            if len(gauges) == 0:
                gauges = self.context.run_model(
                    'curve-fi.all-gauges', {}, return_type=CurveGauges)

                gauges = [Account(address=g.address)
                          for g in gauges
                          if g.lp_token.address == pool_info.lp_token_addr]
                _gauges_type = [0] * len(gauges)

        is_meta = self.is_meta(pool_contract.address.checksum)

        return CurvePoolInfo(**(pool_info.dict()),
                             token_prices=token_prices,
                             virtualPrice=virtual_price,
                             A=pool_A,
                             ratio=ratio,
                             chi=chi,
                             is_meta=is_meta,
                             gauges=Accounts(accounts=gauges))


@Model.describe(slug="curve-fi.pool-tvl",
                version="1.11",
                display_name="Curve Finance Pool - TVL",
                description="Total amount of TVL",
                category='protocol',
                subcategory='curve',
                input=CurvePool,
                output=TVLInfo)
class CurveFinancePoolTVL(Model):
    def run(self, input: CurvePool) -> TVLInfo:
        pool_info = self.context.run_model('curve-fi.pool-info',
                                           input=input,
                                           return_type=CurvePoolInfo)
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
                version="1.11",
                display_name="Curve Finance Pool Liquidity - All",
                description="The amount of Liquidity for Each Token in a Curve Pool - All",
                category='protocol',
                subcategory='curve',
                input=EmptyInputSkipTest,
                output=Some[CurvePoolInfo])
class CurveFinanceAllPoolsInfo(Model):
    def run(self, _) -> Some[CurvePoolInfo]:
        pool_contracts = self.context.run_model(
            'curve-fi.all-pools', {}, return_type=Contracts)

        def _use_for():
            pool_infos = []
            for pool in pool_contracts:
                pool_info = self.context.run_model(
                    'curve-fi.pool-info',
                    pool,
                    return_type=CurvePoolInfo)
                pool_infos.append(pool_info)
            return pool_infos

        def _use_compose():
            model_slug = 'curve-fi.pool-info'
            all_pools = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': model_slug,
                       'modelInputs': pool_contracts.contracts},
                return_type=MapInputsOutput[Contract, CurvePoolInfo])

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

        # pool_infos = _use_compose()
        pool_infos = _use_for()

        all_pools_info = Some[CurvePoolInfo](some=pool_infos)

        # (pd.DataFrame((all_pools_info.dict())['some'])
        # .to_csv(f'tmp/curve-all-info_{self.context.block_number}.csv'))
        return all_pools_info
