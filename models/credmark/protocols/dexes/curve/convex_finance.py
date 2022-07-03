# pylint: disable=locally-disabled, unused-import

from typing import List

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import (Account, Accounts, Address, Contract,
                                Contracts, Portfolio, Position, Price, Token,
                                Tokens)
from credmark.cmf.types.compose import MapInputsOutput
from credmark.cmf.types.ledger import TransactionTable
from credmark.dto import DTO, EmptyInput
from models.credmark.tokens.token import fix_erc20_token
from models.dtos.price import Many, Prices
from models.dtos.tvl import TVLInfo
from models.tmp_abi_lookup import CRV_REWARD
from web3.exceptions import ABIFunctionNotFound, ContractLogicError

np.seterr(all='raise')


class ConvexPoolInfo(DTO):
    lp_token: Token
    deposit_token:  Token
    gauge: Contract
    crv_rewards: Contract
    stash: Contract
    shutdown: bool
    tvl: int


@Model.describe(slug="convex-fi.booster",
                version="0.0",
                display_name="Convex Finance Pools",
                description="Get All Pools in Convex Finance",
                category='protocol',
                subcategory='convex',
                input=EmptyInput,
                output=Contract)
class ConvexFinanceBooster(Model):
    BOOSTER = {
        1: Address('0xF403C135812408BFbE8713b5A23a04b3D48AAE31')
    }

    def run(self, input: EmptyInput) -> Contract:
        booster = Contract(address=self.BOOSTER[self.context.chain_id])
        _ = booster.abi
        return booster


def fix_crv_reward(crv_rewards):
    try:
        _ = crv_rewards.abi
    except ModelDataError:
        crv_rewards._loaded = True  # pylint:disable=protected-access
        crv_rewards.set_abi(CRV_REWARD)
    return crv_rewards


@Model.describe(slug="convex-fi.all-pool-info",
                version="0.1",
                display_name="Convex Finance Pools",
                description="Get All Pools Information in Convex Finance",
                category='protocol',
                subcategory='convex',
                input=EmptyInput,
                output=Many[ConvexPoolInfo])
class ConvexFinanceAllPools(Model):
    def run(self, _: EmptyInput) -> Many[ConvexPoolInfo]:
        booster = Contract(**self.context.models.convex_fi.booster())
        pool_length = booster.functions.poolLength().call()

        pool_infos = []
        for pp in range(pool_length):
            (lp_token, deposit_token,
             gauge, crv_rewards,
             stash, shutdown) = booster.functions.poolInfo(pp).call()

            crv_reward_contract = Contract(address=crv_rewards)
            crv_reward_contract = fix_crv_reward(crv_reward_contract)
            pool_info = ConvexPoolInfo(lp_token=Token(address=lp_token),
                                       deposit_token=Token(address=deposit_token),
                                       gauge=Contract(address=gauge),
                                       crv_rewards=crv_reward_contract,
                                       stash=Contract(address=stash),
                                       shutdown=shutdown,
                                       tvl=crv_reward_contract.functions.totalSupply().call())
            pool_infos.append(pool_info)

        return Many(some=pool_infos)


@Model.describe(slug="convex-fi.earned",
                version="0.0",
                display_name="Convex Finance - Earned for a user",
                description="Get all earned for an account",
                category='protocol',
                subcategory='convex',
                input=Account,
                output=dict)
class ConvexFinanceEarning(Model):
    def run(self, input: Account) -> dict:
        all_pools = self.context.run_model('convex-fi.all-pool-info',
                                           input=EmptyInput(), return_type=Many[ConvexPoolInfo])

        earnings = []
        for pp in all_pools:
            pp.crv_rewards = fix_crv_reward(pp.crv_rewards)

            balance = pp.crv_rewards.functions.balanceOf(input.address.checksum).call()
            earned = pp.crv_rewards.functions.earned(input.address.checksum).call()
            rewards = pp.crv_rewards.functions.rewards(input.address.checksum).call()
            reward_token = pp.crv_rewards.functions.rewardToken().call()
            # NOTE: pp.crv_rewards.functions.stakingToken() == deposit_token
            user_reward_per_token_paid = (pp.crv_rewards.functions
                                          .userRewardPerTokenPaid(input.address.checksum).call())
            if balance != 0 or earned != 0 or rewards != 0:
                earnings.append(dict(
                    lp_token=pp.lp_token,
                    balance=balance,
                    earned=earned,
                    rewards=rewards,
                    reward_token=reward_token,
                    user_reward_per_token_paid=user_reward_per_token_paid
                ))

        return {'earnings': earnings}
