from typing import List
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types.ledger import TransactionTable

from credmark.dto import (
    DTO,
    EmptyInput,
)

from credmark.cmf.types import (
    Address,
    Account,
    Accounts,
    Contract,
    Token,
    Tokens,
)

# Same for all networks
CURVE_PROVIDER = '0x0000000022D53366457F9d5E68Ec105046FC4383'


@Model.describe(slug='curve-fi.get-registry',
                version='1.0',
                display_name='Curve Finance - Get Registry',
                description='Curve Finance - Get Registry',
                input=EmptyInput,
                output=Contract)
class CurveFinanceGetRegistry(Model):
    def run(self, _) -> Contract:
        provider = Contract(address=Address(CURVE_PROVIDER).checksum)
        reg_addr = provider.functions.get_registry().call()
        return Contract(address=Address(reg_addr).checksum).info


class CurveFiPoolInfo(Contract):
    virtualPrice: int
    tokens: Tokens
    balances: List[int]
    underlying_tokens: Tokens
    A: int
    name: str


class CurveFiPoolInfos(DTO):
    pool_infos: List[CurveFiPoolInfo]


@Model.describe(slug="curve-fi.pool-info",
                version="1.0",
                display_name="Curve Finance Pool Liqudity",
                description="The amount of Liquidity for Each Token in a Curve Pool",
                input=Contract,
                output=CurveFiPoolInfo)
class CurveFinancePoolInfo(Model):
    def run(self, input: Contract) -> CurveFiPoolInfo:
        tokens = Tokens()
        underlying_tokens = Tokens()
        balances = []

        try:
            input.functions.coins(0).call()
        except Exception as _err:
            input = Contract(address=input.address.checksum)

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
                tokens.append(Token(address=tok).info)
            except Exception as _err:
                break

        try:
            a = input.functions.A().call()
            virtual_price = input.functions.get_virtual_price().call()
        except Exception as _err:
            virtual_price = (10**18)
            a = 0

        try:
            name = input.functions.name().call()
        except Exception as _err:
            name = ""

        return CurveFiPoolInfo(**(input.dict()),
                               virtualPrice=virtual_price,
                               tokens=tokens,
                               balances=balances,
                               underlying_tokens=underlying_tokens,
                               A=a,
                               name=name)


@Model.describe(slug="curve-fi.all-pools",
                version="1.0",
                display_name="Curve Finance Pool Liqudity",
                description="The amount of Liquidity for Each Token in a Curve Pool",
                output=CurveFiPoolInfos)
class CurveFinanceTotalTokenLiqudity(Model):

    def run(self, input) -> CurveFiPoolInfos:
        registry = self.context.run_model('curve-fi.get-registry',
                                          input=EmptyInput(),
                                          return_type=Contract)

        total_pools = registry.functions.pool_count().call()
        pool_contracts = [
            Contract(address=registry.functions.pool_list(i).call())
            for i in range(0, total_pools)]

        pool_infos = [
            CurveFiPoolInfo(
                **self.context.models.curve_fi.pool_info(
                    Contract(address=pool.address)))
            for pool in pool_contracts]

        return CurveFiPoolInfos(pool_infos=pool_infos)


@Model.describe(slug="curve-fi.all-gauges",
                version='1.0',
                display_name="Curve Finance Gauge List",
                description="All Gauge Contracts for Curve Finance Pools")
class CurveFinanceAllGauges(Model):
    def run(self, input):
        gauge_controller = Contract(address='0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB')
        gauges = []
        i = 0
        while True:
            address = gauge_controller.functions.gauges(i).call()
            if address == Address.null():
                break
            gauges.append(Contract(address=address))
            i += 1

        return gauges


@Model.describe(slug='curve-fi.all-gauge-claim-addresses',
                version='1.0',
                input=Contract,
                output=Accounts)
class CurveFinanceAllGaugeAddresses(Model):

    def run(self, input: Contract) -> Accounts:
        addrs = self.context.ledger.get_transactions(
            columns=[TransactionTable.Columns.FROM_ADDRESS],
            where=f'{TransactionTable.Columns.TO_ADDRESS}=\'{input.address.lower()}\'')
        return Accounts(accounts=[
            Account(address=address)
            for address in
            list(dict.fromkeys([
                a[TransactionTable.Columns.FROM_ADDRESS]
                for a
                in addrs]))])


@Model.describe(slug='curve-fi.get-gauge-stake-and-claimable-rewards',
                version='1.0',
                input=Contract)
class CurveFinanceGaugeRewardsCRV(Model):
    def run(self, input: Contract) -> dict:
        yields = []

        all_addrs = Accounts(**self.context.models.curve_fi.all_gauge_claim_addresses(input))
        for addr in all_addrs.accounts:
            if not addr.address:
                raise ModelRunError(f'Input is invalid, {input}')

            claimable_tokens = input.functions.claimable_tokens(addr.address.checksum).call()
            balanceOf = input.functions.balanceOf(addr.address.checksum).call()
            working_balances = input.functions.working_balances(addr.address.checksum).call()

            yields.append({
                "claimable_tokens": claimable_tokens,
                "balanceOf": balanceOf,
                "working_balances": working_balances,
                "address": addr.address
            })
        return {"yields": yields}


CRV_PRICE = 3.0


@ Model.describe(slug='curve-fi.gauge-yield',
                 version='1.0',
                 input=Contract)
class CurveFinanceAverageGaugeYield(Model):
    def run(self, input: Contract) -> dict:
        """
        presuming that crv has a constant value of $3
        """

        pool_info = self.context.models.curve_fi.pool_info(
            Contract(address=input.functions.lp_token().call()))

        # addrs = self.context.run_model('curve-fi.all-gauge-addresses', input)

        # gauge_input = {
        #     "gaugeAddress": input.address,
        #     "userAddresses": [{"address": a['from_address']} for a in addrs['data']]
        # }

        res = self.context.historical.run_model_historical(
            'curve-fi.get-gauge-stake-and-claimable-rewards',
            window='60 days',
            interval='7 days',
            model_input=input)

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
                            virtual_price = pool_info['virtualPrice'] / (10**18) / (10**18)
                            y2_liquidity_value = y2["balanceOf"] * virtual_price
                            y1_liquidity_value = y1["balanceOf"] * virtual_price
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


@ Model.describe(slug='curve-fi.all-yield', version='1.0')
class CurveFinanceAllYield(Model):
    def run(self, input) -> dict:
        res = []
        # FRAX Liquidity Gauge
        gauges = ['0x72E158d38dbd50A483501c24f792bDAAA3e7D55C']

        # pylint: disable=line-too-long
        # gauges = ["0xbFcF63294aD7105dEa65aA58F8AE5BE2D9d0952A","0xd662908ADA2Ea1916B3318327A97eB18aD588b5d", "0x9582C4ADACB3BCE56Fea3e590F05c3ca2fb9C477",
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
            yields = self.context.run_model('curve-fi.gauge-yield', Token(address=gauge))
            self.logger.info(yields)
            res.append(yields)

        return {"results": res}
