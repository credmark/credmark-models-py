# pylint: disable=locally-disabled, line-too-long
from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract, Token
from credmark.dto import DTO, EmptyInput
from models.tmp_abi_lookup import DAI_ADDRESS


class UniswapQuoterPriceUsd(DTO):
    tokenAddress: Address


@Model.describe(slug='uniswap.quoter-price-dai',
                version='1.0',
                display_name='The Price of a Token on Uniswap in USD',
                description='The Trading Price with respect to USD on Uniswap\'s Frontend)',
                input=UniswapQuoterPriceUsd)
class UniswapRouterPricePair(Model):
    UNISWAP_V3_QUOTER_ADDRESS = {
        1: Address('0xb27308f9f90d607463bb33ea1bebb41c27ce5ab6')
    }

    def run(self, input: UniswapQuoterPriceUsd) -> dict:
        """
        We should be able to hit the IQuoter Interface to get the quoted price from Uniswap.
        Block_number should be taken care of.
        """
        inToken = Token(address=Address(DAI_ADDRESS))
        outToken = Token(address=input.tokenAddress)

        tokenAmount = 1 * 10 ** outToken.decimals
        fee = 10000
        sqrtPriceLimitX96 = 0

        uniswap_quoter_addr = self.UNISWAP_V3_QUOTER_ADDRESS[self.context.chain_id]
        uniswap_quoter = Contract(address=uniswap_quoter_addr)

        quote = uniswap_quoter.functions.quoteExactOutputSingle(inToken.address,
                                                                outToken.address,
                                                                fee,
                                                                tokenAmount,
                                                                sqrtPriceLimitX96).call()

        result = {'value': inToken.scaled(quote)}
        return result


@Model.describe(slug='uniswap.router',
                version='1.0',
                display_name='The Price of a Token on Uniswap with respect to another Token',
                description='The Trading Price with respect to another Token on Uniswap\'s Frontend)',
                input=EmptyInput,
                output=Contract)
class UniswapRouterPriceUsd(Model):
    UNISWAP_V3_SWAP_ROUTER_ADDRESS = {
        1: '0xE592427A0AEce92De3Edee1F18E0157C05861564'
    }

    def run(self, _) -> Contract:
        """
        We should be able to hit the IQuoter Interface to get the quoted price from Uniswap,
         default to USDC/USDT/DAI and throw out outliers.
        """
        uniswap_router_addr = Address(self.UNISWAP_V3_SWAP_ROUTER_ADDRESS[self.context.chain_id])
        return Contract(address=uniswap_router_addr)


@Model.describe(slug='uniswap.tokens',
                version='1.0',
                display_name='uniswap tokens',
                description='uniswap tokens')
class UniswapTokens(Model):
    UNISWAP_FACTORY_ADDRESS = {
        1: Address('0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f')
    }

    def run(self, input) -> dict:
        uniswap_factory_addr = self.UNISWAP_FACTORY_ADDRESS[self.context.chain_id]
        uniswap_factory_contract = Contract(address=uniswap_factory_addr)

        # returns a count of all the trading pairs on uniswap
        allPairsLength = uniswap_factory_contract.functions.allPairsLength().call()

        return {'value': allPairsLength}


@Model.describe(slug='uniswap.exchange',
                version='1.0',
                display_name='uniswap.exchange',
                description='uniswap.exchange')
class UniswapExchange(Model):
    UNISWAP_DAI_V1_ADDRESS = {
        1: Address('0x2a1530C4C41db0B0b2bB646CB5Eb1A67b7158667')
    }

    def run(self, input) -> dict:
        uniswap_dai_v1_addr = Address(self.UNISWAP_DAI_V1_ADDRESS[self.context.chain_id])
        exchange_contract = Contract(address=uniswap_dai_v1_addr)

        # Prices
        eth_amount = self.context.web3.toWei('1', 'Ether')

        bid_daiAmount = exchange_contract.functions.getEthToTokenInputPrice(eth_amount).call()
        bid_price = self.context.web3.toWei(bid_daiAmount, 'Ether') / eth_amount / eth_amount

        offer_daiAmount = exchange_contract.functions.getTokenToEthOutputPrice(eth_amount).call()
        offer_price = self.context.web3.toWei(offer_daiAmount, 'Ether') / eth_amount / eth_amount

        return {'value': (bid_price, offer_price, bid_daiAmount, offer_daiAmount)}
