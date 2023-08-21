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

from models.credmark.protocols.dexes.curve.curve_meta import CurveFiAllGaugesOutput, CurveMeta, CurvePoolContract
from models.dtos.tvl import TVLInfo

np.seterr(all='raise')

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
                version='1.3',
                display_name='Curve Finance - Get Provider',
                description='Get provider contract',
                category='protocol',
                subcategory='curve',
                output=Contract)
class CurveFinanceGetProvider(CurveMeta):
    def run(self, _) -> Contract:
        return self.get_provider()


@Model.describe(slug='curve-fi.get-registry',
                version='1.3',
                display_name='Curve Finance - Get Registry',
                description='Query provider to get the registry',
                category='protocol',
                subcategory='curve',
                output=Contract)
class CurveFinanceGetRegistry(CurveMeta):
    def run(self, _) -> Contract:
        return self.get_registry()


@Model.describe(slug="curve-fi.get-gauge-controller",
                version='1.3',
                display_name="Curve Finance - Get Gauge Controller",
                description="Query the registry for the gauge controller",
                category='protocol',
                subcategory='curve',
                output=Contract)
class CurveFinanceGetGauge(CurveMeta):
    def run(self, _):
        return self.get_gauge_controller()


@Model.describe(slug="curve-fi.all-pools",
                version="1.4",
                display_name="Curve Finance - Get all pools",
                description="Query the registry for all pools",
                category='protocol',
                subcategory='curve',
                output=Contracts)
class CurveFinanceAllPools(CurveMeta):
    def run(self, _) -> Contracts:
        registry = self.get_registry()
        total_pools = registry.functions.pool_count().call()
        pool_contracts = [None] * total_pools
        for i in range(0, total_pools):
            pool_contracts[i] = self.fix_pool(
                Contract(address=registry.functions.pool_list(i).call()))
            _abi = pool_contracts[i].abi
        return Contracts(contracts=pool_contracts)


@Model.describe(slug="curve-fi.pool-info-tokens",
                version="1.15",
                display_name="Curve Finance Pool - Tokens",
                description="The amount of Liquidity for Each Token in a Curve Pool",
                category='protocol',
                subcategory='curve',
                input=CurvePoolContract,
                output=CurveFiPoolInfoToken)
class CurveFinancePoolInfoTokens(CurveMeta):
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

    def run(self, input: CurvePoolContract) -> CurveFiPoolInfoToken:
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
                input = self.fix_pool(CurvePoolContract(address=input.address))

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
                    provider = self.get_provider()
                    pool_info_addr = Address(provider.functions.get_address(1).call())
                    pool_info_contract = Contract(address=pool_info_addr.checksum)
                    pool_info = (pool_info_contract.functions.get_pool_info(
                        input.address.checksum).call())
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
                version="1.32",
                display_name="Curve Finance Pool Liquidity",
                description="The amount of Liquidity for Each Token in a Curve Pool",
                category='protocol',
                subcategory='curve',
                input=CurvePoolContract,
                output=CurveFiPoolInfo)
class CurveFinancePoolInfo(CurveMeta):
    def run(self, input: CurvePoolContract) -> CurveFiPoolInfo:
        registry = self.get_registry()
        pool_info = self.context.run_model('curve-fi.pool-info-tokens',
                                           input,
                                           return_type=CurveFiPoolInfoToken)

        pool_contract = self.fix_pool(Contract(address=pool_info.address))

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

        gauges, gauges_type = registry.functions.get_gauges(
            input.address.checksum).call()
        gauges = [Account(address=g)
                  for g in gauges if not Address(g).is_null()]
        gauges_type = gauges_type[:len(gauges)]

        if self.context.network == Network.Mainnet:
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
                input=EmptyInputSkipTest,
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

        # pool_infos = _use_compose()
        pool_infos = _use_for()

        all_pools_info = Some[CurveFiPoolInfo](some=pool_infos)

        # (pd.DataFrame((all_pools_info.dict())['some'])
        # .to_csv(f'tmp/curve-all-info_{self.context.block_number}.csv'))
        return all_pools_info
