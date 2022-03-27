# pylint: disable=locally-disabled, line-too-long
import credmark.model
from credmark.types import (
    Address,
    Contract,
    Token
)
from credmark.dto import DTO
from models.tmp_abi_lookup import (UNISWAP_QUOTER_ABI,
                                   UNISWAP_QUOTER_ADDRESS,
                                   DAI_ADDRESS,
                                   UNISWAP_FACTORY_ABI,
                                   UNISWAP_FACTORY_ADDRESS,
                                   UNISWAP_DAI_V1_ABI,
                                   UNISWAP_DAI_V1_ADDRESS,
                                   ERC_20_ABI,
                                   UNISWAP_V3_SWAP_ROUTER_ABI,
                                   UNISWAP_V3_SWAP_ROUTER_ADDRESS)


class UniswapQuoterPriceUsd(DTO):
    tokenAddress: Address


@credmark.model.describe(slug='uniswap.quoter-price-usd',
                         version='1.0',
                         display_name='The Price of a Token on Uniswap in USD',
                         description='The Trading Price with respect to USD on Uniswap\'s Frontend)',
                         input=UniswapQuoterPriceUsd)
class UniswapRouterPricePair(credmark.model.Model):

    def run(self, input: UniswapQuoterPriceUsd) -> dict:
        """
        We should be able to hit the IQuoter Interface to get the quoted price from Uniswap.
        Block_number should be taken care of.
        """
        inTokenAddress = Address(DAI_ADDRESS).checksum
        outTokenAddress = input.tokenAddress.checksum

        # FIXME: remove abi
        decimals = Token(address=outTokenAddress, abi=ERC_20_ABI).decimals

        fee = 10000
        sqrtPriceLimitX96 = 0
        tokenAmount = 1 * 10 ** decimals

        uniswap_quoter = Contract(address=Address(
            UNISWAP_QUOTER_ADDRESS).checksum, abi=UNISWAP_QUOTER_ABI)

        quote = uniswap_quoter.functions.quoteExactOutputSingle(inTokenAddress,
                                                                outTokenAddress,
                                                                fee,
                                                                tokenAmount,
                                                                sqrtPriceLimitX96).call()

        result = {'value': quote / 10 ** 18}
        return result


@credmark.model.describe(slug='uniswap.router-price-usd',
                         version='1.0',
                         display_name='The Price of a Token on Uniswap with respect to another Token',
                         description='The Trading Price with respect to another Token on Uniswap\'s Frontend)')
class UniswapRouterPriceUsd(credmark.model.Model):

    def run(self, input) -> dict:
        """
        We should be able to hit the IQuoter Interface to get the quoted price from Uniswap,
         default to USDC/USDT/DAI and throw out outliers.
        """
        _uniswap_router = Contract(
            address=Address(UNISWAP_V3_SWAP_ROUTER_ADDRESS).checksum,
            abi=UNISWAP_V3_SWAP_ROUTER_ABI)

        return {}


@credmark.model.describe(slug='uniswap.tokens',
                         version='1.0',
                         display_name='uniswap tokens',
                         description='uniswap tokens')
class UniswapTokens(credmark.model.Model):

    def run(self, input) -> dict:
        uniswap_factory_contract = Contract(
            address=Address(UNISWAP_FACTORY_ADDRESS).checksum,
            abi=UNISWAP_FACTORY_ABI)

        # returns a count of all the trading pairs on uniswap
        allPairsLength = uniswap_factory_contract.functions.allPairsLength().call()

        return {'value': allPairsLength}


@credmark.model.describe(slug='uniswap.exchange',
                         version='1.0',
                         display_name='uniswap.exchange',
                         description='uniswap.exchange')
class UniswapExchange(credmark.model.Model):

    def run(self, input) -> dict:
        exchange_contract = Contract(
            address=Address(UNISWAP_DAI_V1_ADDRESS).checksum,
            abi=UNISWAP_DAI_V1_ABI)

        # Prices
        eth_amount = self.context.web3.toWei('1', 'Ether')

        bid_daiAmount = exchange_contract.functions.getEthToTokenInputPrice(eth_amount).call()
        bid_price = self.context.web3.toWei(bid_daiAmount, 'Ether') / eth_amount / eth_amount

        offer_daiAmount = exchange_contract.functions.getTokenToEthOutputPrice(eth_amount).call()
        offer_price = self.context.web3.toWei(offer_daiAmount, 'Ether') / eth_amount / eth_amount

        return {'value': (bid_price, offer_price, bid_daiAmount, offer_daiAmount)}
