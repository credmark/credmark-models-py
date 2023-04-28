# pylint: disable=locally-disabled, unused-import


import numpy as np
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import (Account, Contract, Some,
                                Token,
                                Network)
from credmark.dto import DTO, EmptyInput
from models.tmp_abi_lookup import CRV_REWARD

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
        Network.Mainnet: '0xF403C135812408BFbE8713b5A23a04b3D48AAE31'
    }

    def run(self, input: EmptyInput) -> Contract:
        booster = Contract(address=self.BOOSTER[self.context.network])
        _ = booster.abi
        return booster


def fix_crv_reward(crv_rewards):
    try:
        _ = crv_rewards.abi
    except ModelDataError:
        crv_rewards = Contract(crv_rewards.address).set_abi(
            CRV_REWARD, set_loaded=True)
    return crv_rewards


@Model.describe(slug="convex-fi.all-pool-info",
                version="0.2",
                display_name="Convex Finance Pools",
                description="Get All Pools Information in Convex Finance",
                category='protocol',
                subcategory='convex',
                input=EmptyInput,
                output=Some[ConvexPoolInfo])
class ConvexFinanceAllPools(Model):
    def run(self, _: EmptyInput) -> Some[ConvexPoolInfo]:
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
                                       deposit_token=Token(
                                           address=deposit_token),
                                       gauge=Contract(address=gauge),
                                       crv_rewards=crv_reward_contract,
                                       stash=Contract(address=stash),
                                       shutdown=shutdown,
                                       tvl=crv_reward_contract.functions.totalSupply().call())
            pool_infos.append(pool_info)

        return Some[ConvexPoolInfo](some=pool_infos)


class ConvexPoolEarning(DTO):
    lp_token: Token
    balance: float
    earned: float
    rewards: float
    reward_token: Token
    user_reward_per_token_paid: float


@Model.describe(slug="convex-fi.earned",
                version="0.1",
                display_name="Convex Finance - Earned for a user",
                description="Get all earned for an account",
                category='protocol',
                subcategory='convex',
                input=Account,
                output=Some[ConvexPoolEarning])
class ConvexFinanceEarning(Model):
    def run(self, input: Account) -> Some[ConvexPoolEarning]:
        all_pools = self.context.run_model('convex-fi.all-pool-info',
                                           input=EmptyInput(), return_type=Some[ConvexPoolInfo])

        earnings = []
        for pp in all_pools:
            pp.crv_rewards = fix_crv_reward(pp.crv_rewards)

            balance = pp.crv_rewards.functions.balanceOf(
                input.address.checksum).call()
            earned = pp.crv_rewards.functions.earned(
                input.address.checksum).call()
            rewards = pp.crv_rewards.functions.rewards(
                input.address.checksum).call()
            reward_token = pp.crv_rewards.functions.rewardToken().call()
            # NOTE: pp.crv_rewards.functions.stakingToken() == deposit_token
            user_reward_per_token_paid = (pp.crv_rewards.functions
                                          .userRewardPerTokenPaid(input.address.checksum).call())
            if balance != 0 or earned != 0 or rewards != 0:
                earnings.append(ConvexPoolEarning(
                    lp_token=pp.lp_token,
                    balance=balance,
                    earned=earned,
                    rewards=rewards,
                    reward_token=reward_token,
                    user_reward_per_token_paid=user_reward_per_token_paid

                ))

        return Some[ConvexPoolEarning](some=earnings)
