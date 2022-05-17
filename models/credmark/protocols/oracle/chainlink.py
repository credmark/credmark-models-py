from credmark.cmf.model import Model
from credmark.cmf.types import Contract, Price
from credmark.dto import  EmptyInput


@Model.describe(slug="chainlink.eth-usd",
                version="1.0",
                display_name="Chainlink - ETH / USD",
                description="Chainlink - ETH / USD",
                input=EmptyInput,
                output=Price)
class ChainLinkETHUSD(Model):
    CHAINLINK_ETH_USD = {
        1: '0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419',
        4: '0x8A753747A1Fa494EC906cE90E9f37563A8AF630e',  # Rinkeby
        42: '0x9326BFA02ADD2366b30bacB125260Af641031331',  # Kovan
    }

    def run(self, _) -> Price:
        oracle = Contract(address=self.CHAINLINK_ETH_USD[self.context.chain_id])
        (_roundId, answer,
         _startedAt, _updatedAt, _answeredInRound) = oracle.functions.latestRoundData().call()
        decimals = oracle.functions.decimals().call()
        return Price(price=answer / (10 ** decimals),
                     src=f'{self.slug}')


@Model.describe(slug="chainlink.btc-usd",
                version="1.0",
                display_name="Chainlink - BTC / USD",
                description="Chainlink - BTC / USD",
                input=EmptyInput,
                output=Price)
class ChainLinkBTCUSD(Model):
    CHAINLINK_BTC_USD = {
        1: '0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c',
        4: '0xECe365B379E1dD183B20fc5f022230C044d51404',  # Rinkeby
        42: '0x6135b13325bfC4B00278B4abC5e20bbce2D6580e',  # Kovan
    }

    def run(self, _) -> Price:
        oracle = Contract(address=self.CHAINLINK_BTC_USD[self.context.chain_id])
        (_roundId, answer,
         _startedAt, _updatedAt, _answeredInRound) = oracle.functions.latestRoundData().call()
        decimals = oracle.functions.decimals().call()
        return Price(price=answer / (10 ** decimals),
                     src=f'{self.slug}')
