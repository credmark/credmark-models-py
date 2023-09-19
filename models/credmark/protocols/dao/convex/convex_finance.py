# pylint: disable=locally-disabled


import numpy as np
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import Account, Contract, Network, Some, Token
from credmark.dto import DTO

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
                output=Contract)
class ConvexFinanceBooster(Model):
    BOOSTER = {
        Network.Mainnet: '0xF403C135812408BFbE8713b5A23a04b3D48AAE31'
    }

    def run(self, _) -> Contract:
        booster = Contract(address=self.BOOSTER[self.context.network])
        _1 = booster.abi
        return booster


def fix_crv_reward(crv_rewards):
    crv_rewards = Contract(crv_rewards.address).set_abi(
        CRV_REWARD, set_loaded=True)
    return crv_rewards


@Model.describe(slug="convex-fi.all-pool-info",
                version="0.2",
                display_name="Convex Finance Pools",
                description="Get All Pools Information in Convex Finance",
                category='protocol',
                subcategory='convex',
                output=Some[ConvexPoolInfo])
class ConvexFinanceAllPools(Model):
    def run(self, _) -> Some[ConvexPoolInfo]:
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


class ConvexAccount(Account):
    class Config:
        schema_extra = {
            'example': {'address': '0x5291fBB0ee9F51225f0928Ff6a83108c86327636'}
        }


@Model.describe(slug="convex-fi.earned",
                version="0.2",
                display_name="Convex Finance - Earned for a user",
                description="Get all earned for an account",
                category='protocol',
                subcategory='convex',
                input=ConvexAccount,
                output=Some[ConvexPoolEarning])
class ConvexFinanceEarning(Model):
    def run(self, input: Account) -> Some[ConvexPoolEarning]:
        all_pools = self.context.run_model('convex-fi.all-pool-info',
                                           {}, return_type=Some[ConvexPoolInfo])

        m = self.context.multicall

        calls = []
        for pp in all_pools:
            pp.crv_rewards = fix_crv_reward(pp.crv_rewards)
            calls.append(pp.crv_rewards.functions.balanceOf(input.address.checksum))
            calls.append(pp.crv_rewards.functions.earned(input.address.checksum))
            calls.append(pp.crv_rewards.functions.rewards(input.address.checksum))
            calls.append(pp.crv_rewards.functions.rewardToken())
            # NOTE: pp.crv_rewards.functions.stakingToken() == deposit_token
            calls.append(pp.crv_rewards.functions.userRewardPerTokenPaid(input.address.checksum))

        results = m.try_aggregate_unwrap(calls)

        i = 0
        earnings = []
        for pp in all_pools:
            balance = results[i]
            i += 1
            earned = results[i]
            i += 1
            rewards = results[i]
            i += 1
            reward_token = results[i]
            i += 1
            user_reward_per_token_paid = results[i]
            i += 1

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
