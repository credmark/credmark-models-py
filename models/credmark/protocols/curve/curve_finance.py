
from logging import info
from typing import List
import credmark.model
from datetime import datetime

from credmark.types import Account, Address, Contract, Contracts, Token, Tokens
from credmark.types.models.ledger import (TransactionTable)
from credmark.types.dto import DTO, DTOField
from pandas import interval_range
from ....tmp_abi_lookup import CURVE_GAUGE_V1_ABI, CURVE_SWAP_ABI_1, CURVE_SWAP_ABI_2, CURVE_REGISTRY_ADDRESS, CURVE_REGISTRY_ABI, CURVE_GAUGUE_CONTROLLER_ABI
from models.tmp_abi_lookup import CURVE_REGISTRY_ADDRESS, CURVE_REGISTRY_ABI


class CurveFiPoolInfo(Contract):
    virtualPrice: int
    tokens: Tokens
    balances: List[int]
    underlying_tokens: Tokens
    A: int
    name: str


class CurveFiPoolInfos(DTO):
    pool_infos: List[CurveFiPoolInfo]


@credmark.model.describe(slug='curve-fi-pool-historical-reserve',
                         version='1.0',
                         display_name='Curve Finance Pool Reserve Ratios',
                         description="the historical reserve ratios for a curve pool",
                         input=Contract)
class CurveFinanceReserveRatio(credmark.model.Model):

    def run(self, input: Contract) -> dict:
        pool_address = input.address
        pool_contract = self.context.web3.eth.contract(
            address=pool_address.checksum,
            abi=CURVE_SWAP_ABI_1
        )
        res = self.context.historical.run_model_historical('curve-fi-pool-info',
                                                           window='60 days',
                                                           interval='7 days',
                                                           model_input={
                                                               "address": input.address,
                                                           })
        info_i_want = []
        for r in res:
            info_i_want.append({
                "name":r.output['name'],
                "blockNumber":r.blockNumber,
                "balances":r.output['balances'],
                "virtualPrice":r.output['virtualPrice']
            })
        return res


@credmark.model.describe(slug="curve-fi-pool-info",
                         version="1.0",
                         display_name="Curve Finance Pool Liqudity",
                         description="The amount of Liquidity for Each Token in a Curve Pool",
                         input=Contract,
                         output=CurveFiPoolInfo)
class CurveFinancePoolInfo(credmark.model.Model):

    def run(self, input: Contract) -> CurveFiPoolInfo:

        tokens = Tokens()
        underlying_tokens = Tokens()
        balances = []
        try:
            input.functions.coins(0).call()
        except Exception:
            input = Contract(address=input.address, abi=CURVE_SWAP_ABI_2)
        for i in range(0, 8):
            try:
                tok = input.functions.coins(i).call()
                bal = input.functions.balances(i).call()
                try:
                    und = input.functions.underlying_coins(i).call()
                    underlying_tokens.append(Token(address=und))
                except Exception:
                    pass
                balances.append(bal)
                tokens.append(Token(address=tok))
            except Exception:
                break

        try:
            a = input.functions.A().call()
            virtual_price = input.functions.get_virtual_price().call()
        except:
            virtual_price = (10**18)
            a = 0
        try:
            input.name = input.functions.name().call()
        except:
            input.name = "swappool"
        return CurveFiPoolInfo(**(input.dict()),
                               virtualPrice=virtual_price,
                               tokens=tokens,
                               balances=balances,
                               underlying_tokens=underlying_tokens,
                               A=a)


@credmark.model.describe(slug="curve-fi-all-pool-info",
                         version="1.0",
                         display_name="Curve Finance Pool Liqudity",
                         description="The amount of Liquidity for Each Token in a Curve Pool",
                         input=None)
class CurveFinanceTotalTokenLiqudity(credmark.model.Model):

    def run(self, input) -> CurveFiPoolInfos:
        info_i_want = []
        pool_infos = [
            self.context.run_model(
                "curve-fi-pool-info",
                Contract(address=pool.address, abi=CURVE_SWAP_ABI_1),
                return_type=CurveFiPoolInfo)
            for pool in
            self.context.run_model(
                "curve-fi-pools",
                return_type=Contracts)]
        for pi in pool_infos:
            info_i_want.append({
                "address": pi.address,
                "name": pi.name,
                "virtual price": pi.virtualPrice,
                "balances": pi.balances
            })
       

        return info_i_want


@credmark.model.describe(slug="curve-fi-pools",
                         version="1.0",
                         display_name="Curve Finance Pool Liqudity",
                         description="The amount of Liquidity for Each Token in a Curve Pool",
                         input=None,
                         output=Contracts)
class CurveFinancePools(credmark.model.Model):

    def run(self, input) -> Contracts:
        registry = self.context.web3.eth.contract(
            address=Address(CURVE_REGISTRY_ADDRESS).checksum,
            abi=CURVE_REGISTRY_ABI)
        total_pools = registry.functions.pool_count().call()
        return Contracts(
            contracts=[
                Contract(address=registry.functions.pool_list(i).call())
                for i in range(0, total_pools)])


@credmark.model.describe(slug='curve-fi-historical-lp-dist',
                         version='1.0',
                         input=Contract)
class CurveFinanceHistoricalLPDist(credmark.model.Model):

    def run(self, input: Contract) -> dict:
        addrs = self.context.ledger.get_transactions(
            columns=[TransactionTable.Columns.FROM_ADDRESS],
            where=f'{TransactionTable.Columns.TO_ADDRESS}=\'{input.address.lower()}\'')

        gauge = self.context.web3.eth.contract(
            address=Address(input['gaugeAddress']).checksum, abi=CURVE_GAUGE_V1_ABI)


@credmark.model.describe(slug='curve-fi-all-gauge-addresses',
                         version='1.0',
                         input=Contract)
class CurveFinanceAllGaugeAddresses(credmark.model.Model):

    def run(self, input: Contract) -> dict:
        addrs = self.context.ledger.get_transactions(
            columns=[TransactionTable.Columns.FROM_ADDRESS],
            where=f'{TransactionTable.Columns.TO_ADDRESS}=\'{input.address.lower()}\'')
        return addrs


@credmark.model.describe(slug='curve-fi-get-gauge-stake-and-claimable-rewards', version='1.0')
class CurveFinanceGaugeRewardsCRV(credmark.model.Model):
    def run(self, input: dict) -> dict:

        gauge = self.context.web3.eth.contract(
            address=Address(input['gaugeAddress']).checksum, abi=CURVE_GAUGE_V1_ABI)
        yields = []
        for addr in input['userAddresses']:
            claimable_tokens = gauge.functions.claimable_tokens(
                self.context.web3.toChecksumAddress(addr['address'])).call()
            balanceOf = gauge.functions.balanceOf(
                self.context.web3.toChecksumAddress(addr['address'])).call()
            working_balances = gauge.functions.working_balances(
                self.context.web3.toChecksumAddress(addr['address'])).call()

            yields.append({
                "claimable_tokens": claimable_tokens,
                "balanceOf": balanceOf,
                "working_balances": working_balances,
                "address": addr['address']
            })
        return {"yields": yields}


CRV_PRICE = 3.0


@credmark.model.describe(slug='curve-fi-avg-gauge-yield', version='1.0', input=Token)
class CurveFinanceAverageGaugeYield(credmark.model.Model):
    def run(self, input: Token) -> dict:
        """
        presuming that crv has a constant value of $3
        """

        lp_token_address = self.context.web3.eth.contract(
            address=input.address.checksum, abi=CURVE_GAUGE_V1_ABI).functions.lp_token().call()

        pool_info = self.context.run_model(
            'curve-fi-pool-info', Token(address=lp_token_address))
        addrs = self.context.run_model('curve-fi-all-gauge-addresses', input)

        res = self.context.historical.run_model_historical('curve-fi-get-gauge-stake-and-claimable-rewards',
                                                           window='60 days',
                                                           interval='7 days',
                                                           model_input={
                                                               "gaugeAddress": input.address,
                                                               "userAddresses": [{"address": a['from_address']} for a in addrs['data']]
                                                           })
        yields = []
        for idx in range(0, len(res.series) - 1):
            for y1 in res.series[idx].output['yields']:
                if y1['working_balances'] == 0:
                    continue
                if y1['balanceOf'] == 0:
                    continue
                if y1['claimable_tokens'] == 0:
                    continue
                for y2 in res.series[idx + 1].output['yields']:
                    if y1['address'] == y2['address']:
                        if y2['working_balances'] == 0:
                            continue
                        if y2['balanceOf'] == 0:
                            continue
                        if y2['claimable_tokens'] == 0:
                            continue
                        if y1['balanceOf'] == y2['balanceOf']:

                            y2_rewards_value = y2["claimable_tokens"] * CRV_PRICE / (10**18)
                            y1_rewards_value = y1["claimable_tokens"] * CRV_PRICE / (10**18)
                            y2_liquidity_value = y2["balanceOf"] * \
                                pool_info['virtualPrice'] / (10**18) / (10**18)
                            y1_liquidity_value = y1["balanceOf"] * \
                                pool_info['virtualPrice'] / (10**18) / (10**18)
                            new_portfolio_value = y2_rewards_value + y2_liquidity_value
                            old_portfolio_value = y1_rewards_value + y1_liquidity_value
                            if old_portfolio_value > new_portfolio_value:
                                break
                            yields.append(
                                (new_portfolio_value - old_portfolio_value) / old_portfolio_value)
                            break
        if len(yields) == 0:
            return {}
        avg_yield = sum(yields) / len(yields) * (365 * 86400) / (10 * 86400)
        return {"pool_info": pool_info, "crv_yield": avg_yield}


@credmark.model.describe(slug='curve-fi-all-yield', version='1.0')
class CurveFinanceAllYield(credmark.model.Model):
    def run(self, input) -> dict:
        res = []
        gauges = ['0x72E158d38dbd50A483501c24f792bDAAA3e7D55C']
        # gauges = ["0xbFcF63294aD7105dEa65aA58F8AE5BE2D9d0952A", "0xd662908ADA2Ea1916B3318327A97eB18aD588b5d", "0x9582C4ADACB3BCE56Fea3e590F05c3ca2fb9C477",
        #          "0x6d10ed2cF043E6fcf51A0e7b4C2Af3Fa06695707", "0xdFc7AdFa664b08767b735dE28f9E84cd30492aeE", "0x69Fb7c45726cfE2baDeE8317005d3F94bE838840", "0x7ca5b0a2910B33e9759DC7dDB0413949071D7575",
        #          "0xAEA6c312f4b3E04D752946d329693F7293bC2e6D", "0x90Bb609649E0451E5aD952683D64BD2d1f245840", "0x72e158d38dbd50a483501c24f792bdaaa3e7d55c", "0xC5cfaDA84E902aD92DD40194f0883ad49639b023",
        #          "0x4c18E409Dc8619bFb6a1cB56D114C3f592E0aE79", "0x2db0E83599a91b508Ac268a6197b8B14F5e72840", "0x5f626c30EC1215f4EdCc9982265E8b1F411D1352", "0x11137B10C210b579405c21A07489e28F3c040AB1",
        #          "0x64E3C23bfc40722d3B649844055F1D51c1ac041d", "0xF5194c3325202F456c95c1Cf0cA36f8475C1949F", "0xFD4D8a17df4C27c1dD245d153ccf4499e806C87D",
        #          "0xd7d147c6Bb90A718c3De8C0568F9B560C79fa416", "0xB1F2cdeC61db658F091671F5f199635aEF202CAC", "0x4dC4A289a8E33600D8bD4cf5F6313E43a37adec7", "0x462253b8F74B72304c145DB0e4Eebd326B22ca39",
        #          "0x705350c4BcD35c9441419DdD5d2f097d7a55410F", "0x3C0FFFF15EA30C35d7A85B85c0782D6c94e1d238", "0x182B723a58739a9c974cFDB385ceaDb237453c28", "0xA90996896660DEcC6E997655E065b23788857849",
        #          "0x824F13f1a2F29cFEEa81154b46C0fc820677A637", "0x6828bcF74279eE32f2723eC536c22c51Eed383C6", "0x6955a55416a06839309018A8B0cB72c4DDC11f15", "0xC2b1DF84112619D190193E48148000e3990Bf627",
        #          "0xF98450B5602fa59CC66e1379DFfB6FDDc724CfC4", "0x055be5DDB7A925BfEF3417FC157f53CA77cA7222", "0xBC89cd85491d81C6AD2954E6d0362Ee29fCa8F53", "0x3B7020743Bc2A4ca9EaF9D0722d42E20d6935855",
        #          "0xFA712EE4788C042e2B7BB55E6cb8ec569C4530c1", "0x8101E6760130be2C8Ace79643AB73500571b7162"]
        for gauge in gauges:
            print(gauge)
            yields = self.context.run_model(
                'curve-fi-avg-gauge-yield', Contract(address=gauge))
            print(yields)
            res.append(yields)

        return {"results": res}
