from credmark.cmf.model import Model
from credmark.dto import EmptyInput

from models.credmark.protocols.lending.aave.aave_v2 import AaveDebtInfos
from models.credmark.protocols.lending.compound.compound_v2 import CompoundV2PoolInfos


@Model.describe(slug="finance.min-risk-rate",
                version="1.0",
                display_name="Calculate minimal risk rate",
                description='Rates from stablecoins\' loans to Aave and Compound, '
                            'then weighted by their debt size and total supply',
                input=EmptyInput,
                output=dict)
class Minrisk(Model):
    """
    Doc is
        https://docs.credmark.com/smart-money-in-defi/investment-concepts/minimum-risk-rate-of-defi
    """
    STABLECOINS = {
        "USDT": '0xdac17f958d2ee523a2206206994597c13d831ec7',
        "USDC": '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
        "DAI": '0x6b175474e89094c44da98b954eedeac495271d0f',
    }

    def run(self, _) -> dict:
        aave_debts = self.context.run_model('aave-v2.lending-pool-assets',
                                            input=EmptyInput(),
                                            return_type=AaveDebtInfos)

        sb_debt_infos = {}
        sb_tokens = {}
        for dbt in aave_debts:
            token = dbt.token
            if token.address in self.STABLECOINS.values():
                dbt_info = sb_debt_infos.get(token.address, [])
                rate = dbt.supplyRate
                supply_qty = dbt.totalSupply_qty
                sb_debt_infos[token.address] = dbt_info + [(rate, supply_qty)]
                sb_tokens[token.address] = dbt.token

        compound_debts = self.context.run_model('compound-v2.all-pools-info',
                                                input=EmptyInput(),
                                                return_type=CompoundV2PoolInfos)

        for dbt in compound_debts:
            token = dbt.token
            if token.address in self.STABLECOINS.values():
                dbt_info = sb_debt_infos.get(token.address, [])
                rate = dbt.supplyAPY
                supply_qty = dbt.totalLiability
                sb_debt_infos[token.address] = dbt_info + [(rate, supply_qty)]

        weighted_supply = 0
        all_sb_supply = 0
        for sb_address, info in sb_debt_infos.items():
            weighted_rate = sum([r * q for r, q in info]) / sum([q for _r, q in info])
            scaled_supply = sb_tokens[sb_address].scaled(sb_tokens[sb_address].total_supply)
            weighted_supply += weighted_rate * scaled_supply
            all_sb_supply += scaled_supply

        supply_weighted_rate = weighted_supply / all_sb_supply
        return {'min_risk_rate': supply_weighted_rate}
