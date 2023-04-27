# pylint:disable=unused-import, invalid-name

from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract, Network, Token
from credmark.dto import DTO


class ConvexPoolInput(DTO):
    lp_token: Address
    reward: Address


@Model.describe(slug="contrib.curve-convex-yield",
                display_name="APR for Convex pool",
                description="base, crv, cvx apr for convex pool",
                input=ConvexPoolInput,
                version="1.1",
                developer="megaflare14",
                category="protocol",
                subcategory="curve",
                output=dict,
                )
class ConvexPoolApr(Model):
    # This is a re-implementation of the convex subgraph from:
    # https://github.com/convex-community/convex-subgraph/blob/e9c5cdfae055802af99b545739d9cf67a2a4c2cd/subgraphs/curve-pools/src/services/pools.ts#L253
    CRV_ADDRESS = {
        Network.Mainnet: "0xD533a949740bb3306d119CC777fa900bA034cd52"}
    CVX_ADDRESS = {
        Network.Mainnet: "0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B"}

    CVX_CLIFF_SIZE = 100000
    CVX_CLIFF_COUNT = 1000
    CVX_MAX_SUPPLY = 100000000

    BLOCKS_IN_DAY = 5760
    SECONDS_IN_YEAR = 31536000

    def get_cvx_mint_amount(self, crvPerYear):
        cvx_contract = Token(address=self.CVX_ADDRESS[self.context.network])
        cvx_supply = cvx_contract.total_supply_scaled
        current_cliff = cvx_supply / self.CVX_CLIFF_SIZE
        if current_cliff < self.CVX_CLIFF_COUNT:
            remaining = self.CVX_CLIFF_COUNT - current_cliff
            cvx_earned = crvPerYear * remaining / self.CVX_CLIFF_COUNT
            amount_till_max = self.CVX_MAX_SUPPLY - cvx_supply
            cvx_earned = min(cvx_earned, amount_till_max)
            return cvx_earned
        return 0

    def get_lptoken_price(self, pool_addr, block_number):
        curve_pool_info = self.context.run_model(
            "curve-fi.pool-info",
            {
                "address": pool_addr,
            },
            block_number=block_number
        )
        lp_token = Token(curve_pool_info['lp_token_addr'])
        return lp_token.scaled(curve_pool_info["virtualPrice"])

    def get_base_apr(self, lp_token_addr, currentVirtualPrice):
        previous_vprice = self.get_lptoken_price(lp_token_addr,
                                                 self.context.block_number-self.BLOCKS_IN_DAY)
        if previous_vprice == 0:
            return 0

        return (currentVirtualPrice - previous_vprice) / previous_vprice

    def run(self, input: ConvexPoolInput) -> dict:
        v_price = self.get_lptoken_price(
            input.lp_token, self.context.block_number)
        reward_contract = Contract(address=input.reward)
        finish_period = reward_contract.functions.periodFinish().call()
        supply = reward_contract.functions.totalSupply().call() / 1e18
        virtual_supply = supply * v_price

        base_apr = self.get_base_apr(input.lp_token, v_price)

        # Fetching crv and cvx price from chainlink
        block_number = self.context.block_number
        crv_price = self.context.run_model(
            "price.oracle-chainlink",
            {
                "base": {"address": self.CRV_ADDRESS[self.context.network]},
                "quote": {"symbol": "USD"},
            },
        )["price"]
        cvx_price = self.context.run_model(
            "price.oracle-chainlink",
            {
                "base": {"address": self.CVX_ADDRESS[self.context.network]},
                "quote": {"symbol": "USD"},
            },
        )["price"]

        # Calculating crvApe and cvxApr
        crv_apr = 0
        cvx_apr = 0
        if block_number < finish_period:
            rate = reward_contract.functions.rewardRate().call() / 1e18
            crvPerUnderlying = 0
            if virtual_supply > 0:
                crvPerUnderlying = rate / virtual_supply
            crv_per_year = crvPerUnderlying * self.SECONDS_IN_YEAR
            cvx_per_year = self.get_cvx_mint_amount(crv_per_year)
            crv_apr = crv_per_year * crv_price
            cvx_apr = cvx_per_year * cvx_price

        return {
            "base_apr": base_apr,
            "crv_apr": crv_apr,
            "cvx_apr": cvx_apr,
        }
