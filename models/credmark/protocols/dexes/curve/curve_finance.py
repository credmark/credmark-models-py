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
                version="1.9",
                display_name="Curve Finance - Get all pools",
                description="Query the registry for all pools",
                category='protocol',
                subcategory='curve',
                output=CurvePoolMetas)
class CurveFinanceAllPools(Model, CurveMeta):
    # pylint: disable=too-many-branches
    def run(self, _) -> CurvePoolMetas:
        all_gauges = self.context.run_model('curve-fi.all-gauges', {}, return_type=CurveGauges)
        all_gauges_dict = {g.lp_token.address: g.address for g in all_gauges.contracts}

        m = self.context.multicall
        all_addrs = set()
        pool_contracts = []

        registry = self.get_registry()
        if not registry.address.is_null():
            total_pools = registry.functions.pool_count().call()
            res_addr = m.try_aggregate_unwrap(
                [registry.functions.pool_list(i) for i in range(total_pools)])
            res_is_meta = m.try_aggregate_unwrap(
                [registry.functions.is_meta(res) for res in res_addr])
            res_lp_token = m.try_aggregate_unwrap(
                [registry.functions.get_lp_token(addr) for addr in res_addr])
            assert all(not Address(x).is_null() for x in res_lp_token)

            for pool_address, is_meta, lp_token in zip(res_addr, res_is_meta, res_lp_token):
                gauge_addr = all_gauges_dict.get(pool_address)
                if gauge_addr:
                    gauge = Contract(address=gauge_addr)
                else:
                    gauge = None

                if is_meta:
                    pool_contracts.append(CurvePoolMeta(
                        address=pool_address,
                        pool_type=CurvePoolType.MetaPool,
                        gauge=gauge,
                        lp_token=Token(address=lp_token)))
                else:
                    pool_contracts.append(CurvePoolMeta(
                        address=pool_address,
                        pool_type=CurvePoolType.StableSwap,
                        gauge=gauge,
                        lp_token=Token(address=lp_token)))
                if pool_address in all_addrs:
                    raise ModelDataError(f"Duplicate pool address {pool_address}")
                all_addrs.add(pool_address)
            self.logger.info(f'{len(all_addrs)} from registry')
        del registry

        metapool_factory = self.get_metapool_factory()
        if not metapool_factory.address.is_null():
            total_pools = metapool_factory.functions.pool_count().call()
            duplicated = 0
            res_addr = m.try_aggregate_unwrap(
                [metapool_factory.functions.pool_list(i) for i in range(total_pools)])
            res_is_meta = m.try_aggregate_unwrap(
                [metapool_factory.functions.is_meta(res) for res in res_addr])

            for pool_address, is_meta in zip(res_addr, res_is_meta):
                gauge_addr = all_gauges_dict.get(pool_address)
                if pool_address in all_addrs:
                    self.logger.warning(
                        f"Duplicate pool address {pool_address}/{is_meta} in metapool factory")
                    duplicated += 1
                    continue

                if gauge_addr:
                    gauge = Contract(address=gauge_addr)
                else:
                    gauge = None

                if is_meta:
                    pool_contracts.append(CurvePoolMeta(
                        address=pool_address,
                        pool_type=CurvePoolType.MetaPool,
                        gauge=gauge,
                        lp_token=Token(address=pool_address)))
                else:
                    pool_contracts.append(CurvePoolMeta(
                        address=pool_address,
                        pool_type=CurvePoolType.StableSwap,
                        gauge=gauge,
                        lp_token=Token(address=pool_address)))
                if pool_address in all_addrs:
                    raise ModelDataError(f"Duplicate pool address {pool_address}")
                all_addrs.add(pool_address)
            self.logger.info(
                f'{len(all_addrs)}=+{total_pools} from metapool factory with {duplicated} duplicates')
        del metapool_factory

        cryptoswap_registry = self.get_cryptoswap_registry()
        if not cryptoswap_registry.address.is_null():
            total_pools = cryptoswap_registry.functions.pool_count().call()
            duplicated = 0
            res_addr = m.try_aggregate_unwrap(
                [cryptoswap_registry.functions.pool_list(i) for i in range(total_pools)])
            res_lp_token = m.try_aggregate_unwrap(
                [cryptoswap_registry.functions.get_lp_token(addr) for addr in res_addr])
            assert all(not Address(x).is_null() for x in res_lp_token)

            for pool_address, lp_token in zip(res_addr, res_lp_token):
                gauge_addr = all_gauges_dict.get(pool_address)
                if pool_address in all_addrs:
                    self.logger.warning(
                        f"Duplicate pool address {pool_address} in cryptoswap registry")
                    duplicated += 1
                    continue

                if gauge_addr:
                    gauge = Contract(address=gauge_addr)
                else:
                    gauge = None
                pool_contracts.append(CurvePoolMeta(
                    address=pool_address,
                    pool_type=CurvePoolType.CryptoSwap,
                    gauge=gauge,
                    lp_token=Token(address=lp_token)))
                all_addrs.add(pool_address)
            self.logger.info(
                f'{len(all_addrs)}=+{total_pools} from cryptoswap registry with {duplicated} duplicates')
        del cryptoswap_registry

        cryptoswap_factory = self.get_cryptoswap_factory()
        if not cryptoswap_factory.address.is_null():
            total_pools = cryptoswap_factory.functions.pool_count().call()
            duplicated = 0
            res_addr = m.try_aggregate_unwrap(
                [cryptoswap_factory.functions.pool_list(i) for i in range(total_pools)])
            for pool_address in res_addr:
                if pool_address in all_addrs:
                    self.logger.warning(
                        f"Duplicate pool address {pool_address} in cryptoswap factory")
                    duplicated += 1
                    continue

                gauge_addr = all_gauges_dict.get(pool_address)
                if gauge_addr:
                    gauge = Contract(address=gauge_addr)
                else:
                    gauge = None
                pool_contracts.append(CurvePoolMeta(
                    address=pool_address,
                    pool_type=CurvePoolType.CryptoSwapFactory,
                    gauge=gauge,
                    lp_token=Token(address=pool_address)))
                all_addrs.add(pool_address)
            self.logger.info(
                f'{len(all_addrs)}=+{total_pools} from cryptoswap factory with {duplicated} duplicates')
        del cryptoswap_factory
        return CurvePoolMetas(contracts=pool_contracts)


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
        input = input.get()
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
                input = CurvePool(address=input.address, pool_type=None).get()

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
        pool_contract = pool_info.get()

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
