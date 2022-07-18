from decimal import Decimal, getcontext
from typing import List, NamedTuple

import numpy as np
from credmark.cmf.model import Model
from credmark.cmf.types import (Address, Contract, Contracts, Network, Some,
                                Token, Tokens)
from credmark.dto import DTO, EmptyInput
from models.tmp_abi_lookup import BALANCER_POOL_ABI
from models.utils.math import divDown, divUp, mulUp
from web3.exceptions import ABIFunctionNotFound

np.seterr(all='raise')


class BalancerPoolPriceInfo(DTO):
    class Ratio(DTO):
        token0: Token
        token1: Token
        ratio: float
        tick_liqudity0: float
        tick_liqudity1: float
    tokens: Tokens
    balances: List[float]
    weights: List[int]
    ratios: List[Ratio]

    # 0x32296969Ef14EB0c6d29669C550D4a0449130230


# pylint:disable=invalid-name
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
    prevTokenbalance = 0
    tokenBalance = divUp((invariant*invariant+c), (invariant+b))
    for i in range(255):
        prevTokenbalance = tokenBalance
        tokenBalance = divUp((mulUp(tokenBalance, tokenBalance) + c), ((tokenBalance*Decimal(2))+b-invariant))
        if tokenBalance > prevTokenbalance:
            if tokenBalance-prevTokenbalance <= 1/1e18:
                break
        elif prevTokenbalance-tokenBalance <= 1/1e18:
            break
    return tokenBalance


@ Model.describe(slug='balancer-fi.get-all-pools',
                 version='0.1',
                 display_name='Balancer Finance - Get all pools',
                 description='Get all pools',
                 category='protocol',
                 subcategory='balancer',
                 input=EmptyInput,
                 output=Contracts)
class GetBalancerAllPools(Model):
    VAULT_ADDR = {Network.Mainnet: '0xBA12222222228d8Ba445958a75a0704d566BF2C8'}

    def run(self, _) -> Contracts:
        vault = Contract(address=Address(self.VAULT_ADDR[self.context.network]).checksum)
        with vault.ledger.events.PoolRegistered as q:
            df = q.select(columns=[q.EVT_BLOCK_NUMBER, q.POOLADDRESS],
                          order_by=q.EVT_BLOCK_NUMBER, limit=5000).to_dataframe()

        contracts = []
        for _n, r in df.iterrows():
            pool_addr = r.inp_pooladdress
            pool = Contract(address=pool_addr, abi=BALANCER_POOL_ABI)
            try:
                _pool_id = pool.functions.getPoolId().call()
                print(_n, pool_addr, pool._meta.contract_name)  # pylint:disable=protected-access
                contracts.append(pool)
            except ABIFunctionNotFound:
                print(pool_addr)

        return Contracts(contracts=contracts)


@ Model.describe(slug='balancer-fi.get-all-pools-price-info',
                 version='0.1',
                 display_name='Balancer Finance - Get all pools',
                 description='Get all pools',
                 category='protocol',
                 subcategory='balancer',
                 input=EmptyInput,
                 output=Some[BalancerPoolPriceInfo])
class GetBalancerAllPoolInfo(Model):
    def run(self, _) -> Some[BalancerPoolPriceInfo]:
        pools = self.context.run_model('balancer-fi.get-all-pools',
                                       input=EmptyInput(),
                                       return_type=Contracts)
        pool_infos = []
        for pool in pools:
            pool_info_dto = self.context.run_model(
                slug='balancer-fi.get-pool-price-info',
                input=pool,
                return_type=BalancerPoolPriceInfo)
            pool_infos.append(pool_info_dto)
        return Some(some=pool_infos)


@ Model.describe(slug='balancer-fi.get-pool-price-info',
                 version='0.0',
                 display_name='Balancer Finance - Get pool price info',
                 description='Get price information for a Balancer pool',
                 category='protocol',
                 subcategory='balancer',
                 input=Contract,
                 output=BalancerPoolPriceInfo)
class GetBalancerPoolPriceInfo(Model):
    VAULT_ADDR = {Network.Mainnet: '0xBA12222222228d8Ba445958a75a0704d566BF2C8'}

    class BalancerPoolTokens(NamedTuple):
        tokens_addr: List[Address]
        balances: List[float]
        lastChangeBlock: int

    def run(self, input: Contract) -> BalancerPoolPriceInfo:
        # https://metavision-labs.gitbook.io/balancerv2cad/code-and-instructions/balancer_py_edition/stablemath.py
        # https://token-engineering-balancer.gitbook.io/balancer-simulations/additional-code-and-instructions/arbitrage-agent
        vault = Contract(address=Address(self.VAULT_ADDR[self.context.network]).checksum)

        pool_addr = input.address
        pool = Contract(address=pool_addr)
        _ = pool.abi
        # pool = Contract(address=pool_addr, abi=BALANCER_POOL_ABI)

        pool_id = pool.functions.getPoolId().call()
        pool_info = self.BalancerPoolTokens(*vault.functions.getPoolTokens(pool_id).call())
        tokens = [Token(address=addr) for addr in pool_info.tokens_addr]

        if pool._meta.contract_name == 'MetaStablePool':  # pylint:disable=protected-access
            # TODO: Wrong, this is from the Rate provider (Oracle)
            ratios = input.functions.getScalingFactors().call()
            # amplification = input.functions.getAmplificationParameter().call()
            invariant, amplification = input.functions.getLastInvariant().call()
            invariant = Decimal(invariant)
            amplification = Decimal(amplification)
            balances = [Decimal(f) for f in pool_info.balances]
            _x0 = getTokenBalanceGivenInvariantAndAllOtherBalances(amplification,
                                                                   balances, invariant, 0)
            _x1 = getTokenBalanceGivenInvariantAndAllOtherBalances(amplification,
                                                                   balances, invariant, 1)
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
                tick_liqudity0=liquidity0,
                tick_liqudity1=liquidity1)
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
                    ratio01 = scaled_balance1 / weights[t1] / scaled_balance0 * weights[t0]
                    liquidity0 = (np.abs((np.power(1.001, - weights[t1] / weights[t0] / 2) - 1))
                                  * scaled_balance0)
                    liquidity1 = ((np.power(1.001, 1 - weights[t1] / weights[t0] / 2) - 1)
                                  * scaled_balance1)
                    ratio = BalancerPoolPriceInfo.Ratio(
                        token0=token0,
                        token1=token1,
                        ratio=ratio01,
                        tick_liqudity0=liquidity0,
                        tick_liqudity1=liquidity1)
                    ratios.append(ratio)

        pool_info_dto = BalancerPoolPriceInfo(
            tokens=Tokens(tokens=tokens),
            balances=pool_info.balances,
            weights=weights,
            ratios=ratios
        )

        return pool_info_dto
