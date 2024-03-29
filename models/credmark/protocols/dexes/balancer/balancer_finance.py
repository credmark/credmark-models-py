# pylint:disable=invalid-name

from decimal import Decimal, getcontext
from typing import List, NamedTuple, Optional

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Address, Contract, Contracts, Network, Records, Some, Token, Tokens
from credmark.dto import DTO, DTOField, EmptyInputSkipTest
from web3.exceptions import ABIFunctionNotFound, ContractLogicError

# BALANCER_META_STABLE_POOL_ABI
from models.tmp_abi_lookup import BALANCER_POOL_ABI, BALANCER_VAULT_ABI
from models.utils.math import divDown, divUp, mulUp

np.seterr(all='raise')


class BalancerPoolPriceInfo(DTO):
    class Ratio(DTO):
        token0: Token
        token1: Token
        ratio: float
        tick_liquidity0: float
        tick_liquidity1: float
    tokens: Tokens
    balances: List[float]
    weights: List[int]
    ratios: List[Ratio]

# Lido: Balancer wstETH-ETH Pool
# 0x32296969Ef14EB0c6d29669C550D4a0449130230


def getTokenBalanceGivenInvariantAndAllOtherBalances(
        amplificationParameter: Decimal,
        balances: List[Decimal],
        invariant: Decimal,
        tokenIndex: int) -> Decimal:
    # pylint:disable=line-too-long
    getcontext().prec = 28
    ampTimesTotal = amplificationParameter * len(balances)
    bal_sum = Decimal(sum(balances))
    P_D = len(balances) * balances[0]
    for i in range(1, len(balances)):
        P_D = (P_D*balances[i]*len(balances))/invariant

    bal_sum -= balances[tokenIndex]

    c = invariant*invariant/ampTimesTotal
    c = divUp(mulUp(c, balances[tokenIndex]), P_D)
    b = bal_sum + divDown(invariant, ampTimesTotal)
    prevTokenBalance = 0
    tokenBalance = divUp((invariant*invariant+c), (invariant+b))
    for _i in range(255):
        prevTokenBalance = tokenBalance
        tokenBalance = divUp((mulUp(tokenBalance, tokenBalance) + c),
                             ((tokenBalance*Decimal(2))+b-invariant))
        if tokenBalance > prevTokenBalance:
            if tokenBalance-prevTokenBalance <= 1/1e18:
                break
        elif prevTokenBalance-tokenBalance <= 1/1e18:
            break
    return tokenBalance


@Model.describe(slug='balancer-fi.get-all-pools',
                version='0.6',
                display_name='Balancer Finance - Get all pools',
                description='Get all pools',
                category='protocol',
                subcategory='balancer',
                output=Records)
class GetBalancerAllPools(Model):
    VAULT_ADDR = {
        Network.Mainnet: '0xBA12222222228d8Ba445958a75a0704d566BF2C8'}

    def run(self, _) -> Records:
        vault = Contract(address=Address(
            self.VAULT_ADDR[self.context.network]).checksum)

        with vault.ledger.events.PoolRegistered as q:
            df_ts = []
            offset = 0

            while True:
                df_tt = q.select(columns=[q.BLOCK_NUMBER, q.EVT_POOLADDRESS, q.EVT_POOLID],
                                 order_by=q.BLOCK_NUMBER.comma_(q.EVT_POOLADDRESS),
                                 limit=5000,
                                 offset=offset).to_dataframe()

                if df_tt.shape[0] > 0:
                    df_ts.append(df_tt)

                if df_tt.shape[0] < 5000:
                    break
                offset += 5000
        df_registered = pd.concat(df_ts)

        def _verify_pool():
            contracts = []
            for _n, r in df_registered.iterrows():
                pool_addr = r.evt_poolAddress
                pool = Contract(address=pool_addr).set_abi(
                    BALANCER_POOL_ABI, set_loaded=True)

                try:
                    _pool_id = pool.functions.getPoolId().call()
                    # print(_n, pool_addr, pool._meta.contract_name, file=sys.stderr)  # pylint:disable=protected-access
                    contracts.append(pool)
                except (ABIFunctionNotFound, ContractLogicError):
                    # print(pool_addr, file=sys.stderr)
                    pass
            return Contracts(contracts=contracts)

        return Records.from_dataframe(df_registered)


@Model.describe(slug='balancer-fi.get-all-pools-price-info',
                version='0.4',
                display_name='Balancer Finance - Get all pools',
                description='Get all pools',
                category='protocol',
                subcategory='balancer',
                input=EmptyInputSkipTest,
                output=Some[BalancerPoolPriceInfo])
class GetBalancerAllPoolInfo(Model):
    def run(self, _) -> Some[BalancerPoolPriceInfo]:
        pools = self.context.run_model('balancer-fi.get-all-pools',
                                       {},
                                       return_type=Records).to_dataframe()
        pool_infos = []
        pool_info_slug = 'balancer-fi.get-pool-price-info'
        for row in pools.itertuples():
            pool = BalancerContract(address=row.evt_poolAddress, pool_id=row.evt_poolId)
            try:
                pool_info_dto = self.context.run_model(
                    slug=pool_info_slug,
                    input=pool,
                    return_type=BalancerPoolPriceInfo)
                pool_infos.append(pool_info_dto)
            except ModelRunError:
                # Error with 0x6de69beb66317557e65168bd7d3fff22a89dbb11
                self.logger.warning(
                    'Can not get pool info with %s(%s)', pool_info_slug, pool.address)
                continue
        return Some(some=pool_infos)


class BalancerContract(Contract):
    pool_id: Optional[str] = DTOField(description='Balancer pool id')

    class Config:
        schema_extra = {
            'examples': [{"address": "0x61d5dc44849c9C87b0856a2a311536205C96c7FD"},
                         {"address": "0x647c1FD457b95b75D0972fF08FE01d7D7bda05dF"},
                         {"address": "0x32296969Ef14EB0c6d29669C550D4a0449130230"}, ]
        }


@Model.describe(slug='balancer-fi.get-pool-price-info',
                version='0.3',
                display_name='Balancer Finance - Get pool price info',
                description='Get price information for a Balancer pool',
                category='protocol',
                subcategory='balancer',
                input=BalancerContract,
                output=BalancerPoolPriceInfo)
class GetBalancerPoolPriceInfo(Model):
    VAULT_ADDR = {
        Network.Mainnet: '0xBA12222222228d8Ba445958a75a0704d566BF2C8'}

    class BalancerPoolTokens(NamedTuple):
        tokens_addr: List[Address]
        balances: List[float]
        lastChangeBlock: int

    def run(self, input: BalancerContract) -> BalancerPoolPriceInfo:
        # https://metavision-labs.gitbook.io/balancerv2cad/code-and-instructions/balancer_py_edition/stablemath.py
        # https://token-engineering-balancer.gitbook.io/balancer-simulations/additional-code-and-instructions/arbitrage-agent
        vault = Contract(address=Address(
            self.VAULT_ADDR[self.context.network]).checksum).set_abi(BALANCER_VAULT_ABI)

        pool_addr = input.address
        pool = Contract(address=pool_addr)

        try:
            _ = pool.abi
        except ModelDataError:
            pool = Contract(input.address).set_abi(BALANCER_POOL_ABI, set_loaded=True)

        if input.pool_id is None:
            pool_id = pool.functions.getPoolId().call()
        else:
            pool_id = input.pool_id

        try:
            pool_info = self.BalancerPoolTokens(
                *vault.functions.getPoolTokens(pool_id).call())
        except ABIFunctionNotFound:
            # vault = Contract(vault.functions.getVault().call())
            pool_info = self.BalancerPoolTokens(
                *vault.functions.getPoolTokens(pool_id).call())

        tokens = [Token(address=addr).as_erc20(set_loaded=True) for addr in pool_info.tokens_addr]

        if pool._meta.contract_name == 'MetaStablePool':  # pylint:disable=protected-access

            # TODO: Wrong, this is from the Rate provider (Oracle)
            ratios = input.functions.getScalingFactors().call()
            # amplification = input.functions.getAmplificationParameter().call()
            invariant, amplification = input.functions.getLastInvariant().call()
            invariant = Decimal(invariant)
            amplification = Decimal(amplification)
            balances = [Decimal(f) for f in pool_info.balances]
            _x0 = getTokenBalanceGivenInvariantAndAllOtherBalances(
                amplification, balances, invariant, 0)
            _x1 = getTokenBalanceGivenInvariantAndAllOtherBalances(
                amplification, balances, invariant, 1)
            token0 = tokens[0]
            token1 = tokens[1]
            scaled_balance0 = token1.scaled(pool_info.balances[0])

            # TODO: Wrong, need to derive liquidity.
            scaled_balance1 = token1.scaled(pool_info.balances[1])
            liquidity0 = (np.abs((np.power(1.001, -0.5) - 1))
                          * scaled_balance0)
            liquidity1 = ((np.power(1.001, 0.5) - 1)
                          * scaled_balance1)

            ratio = BalancerPoolPriceInfo.Ratio(
                token0=tokens[0],
                token1=tokens[1],
                ratio=ratios[0] / ratios[1],
                tick_liquidity0=liquidity0,
                tick_liquidity1=liquidity1)
            pool_info_dto = BalancerPoolPriceInfo(
                tokens=Tokens(tokens=tokens),
                balances=pool_info.balances,
                weights=[5, 5],
                ratios=[ratio])
            return pool_info_dto

        weights = pool.functions.getNormalizedWeights().call()

        ratios = []
        n_tokens = len(tokens)
        for t0 in range(n_tokens):
            for t1 in range(n_tokens):
                if t1 > t0:
                    token0 = tokens[t0]
                    token1 = tokens[t1]
                    scaled_balance0 = token1.scaled(pool_info.balances[t0])
                    scaled_balance1 = token1.scaled(pool_info.balances[t1])
                    if scaled_balance0 == 0 or scaled_balance1 == 0:
                        ratio01 = 0
                    else:
                        ratio01 = scaled_balance1 / weights[t1] / scaled_balance0 * weights[t0]
                    liquidity0 = (np.abs((np.power(1.001, - weights[t1] / weights[t0] / 2) - 1))
                                  * scaled_balance0)
                    liquidity1 = ((np.power(1.001, 1 - weights[t1] / weights[t0] / 2) - 1)
                                  * scaled_balance1)
                    ratio = BalancerPoolPriceInfo.Ratio(
                        token0=token0,
                        token1=token1,
                        ratio=ratio01,
                        tick_liquidity0=liquidity0,
                        tick_liquidity1=liquidity1)
                    ratios.append(ratio)

        pool_info_dto = BalancerPoolPriceInfo(
            tokens=Tokens(tokens=tokens),
            balances=pool_info.balances,
            weights=weights,
            ratios=ratios
        )

        return pool_info_dto
