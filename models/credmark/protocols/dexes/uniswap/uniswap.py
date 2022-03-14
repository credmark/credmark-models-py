import credmark.model
from credmark.types import Address
from credmark.types.dto import DTO
from models.tmp_abi_lookup import (uniswap_quoter_abi,
                                   uniswap_quoter_address,
                                   uniswap_factory_abi,
                                   UNISWAP_FACTORY_ADDRESS,
                                   UNISWAP_DAI_V1_ABI,
                                   UNISWAP_DAI_V1_ADDRESS,
                                   MIN_ERC20_ABI,
                                   UNISWAP_V3_SWAP_ROUTER_ABI,
                                   UNISWAP_V3_SWAP_ROUTER_ADDRESS)


class UniswapQuoterPriceUsd(DTO):
    tokenAddress: Address


@credmark.model.describe(slug='uniswap-quoter-price-usd',
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

        uniswap_quoter = self.context.web3.eth.contract(
            address=Address(uniswap_quoter_address).checksum,
            abi=uniswap_quoter_abi)

        decimals = self.context.web3.eth.contract(
            address=Address(input.tokenAddress).checksum,
            abi=MIN_ERC20_ABI).functions.decimals().call()

        tokenIn = '0x6B175474E89094C44Da98b954EedeAC495271d0F'
        tokenOut = input.tokenAddress
        fee = 10000
        sqrtPriceLimitX96 = 0
        tokenAmount = 1 * 10 ** decimals

        quote = uniswap_quoter.functions.quoteExactOutputSingle(tokenIn,
                                                                tokenOut,
                                                                fee,
                                                                tokenAmount,
                                                                sqrtPriceLimitX96).call()

        result = {'value': quote / 10 ** 18}
        return result


@credmark.model.describe(slug='uniswap-router-price-usd',
                         version='1.0',
                         display_name='The Price of a Token on Uniswap with respect to another Token',
                         description='The Trading Price with respect to another Token on Uniswap\'s Frontend)')
class UniswapRouterPriceUsd(credmark.model.Model):

    def run(self, input) -> dict:
        """
        We should be able to hit the IQuoter Interface to get the quoted price from Uniswap, default to USDC/USDT/DAI and throw out outliers.
        """
        uniswap_router = self.context.web3.eth.contract(
            address=Address(UNISWAP_V3_SWAP_ROUTER_ADDRESS).checksum,
            abi=UNISWAP_V3_SWAP_ROUTER_ADDRESS)

        return {}


@credmark.model.describe(slug='uniswap-tokens',
                         version='1.0',
                         display_name='uniswap tokens',
                         description='uniswap tokens')
class UniswapTokens(credmark.model.Model):

    def run(self, input) -> dict:
        uniswap_factory_contract = self.context.web3.eth.contract(
            address=Address(UNISWAP_FACTORY_ADDRESS).checksum,
            abi=uniswap_factory_abi)

        # returns a count of all the trading pairs on uniswap
        allPairsLength = uniswap_factory_contract.functions.allPairsLength().call()

        return {'value': allPairsLength}


@credmark.model.describe(slug='uniswap-exchange',
                         version='1.0',
                         display_name='uniswap-exchange',
                         description='uniswap-exchange')
class UniswapExchange(credmark.model.Model):

    def run(self, input) -> dict:
        exchange_contract = self.context.web3.eth.contract(
            address=Address(UNISWAP_DAI_V1_ADDRESS).checksum,
            abi=UNISWAP_DAI_V1_ABI)

        # Prices
        ETH_AMOUNT = self.context.web3.toWei('1', 'Ether')

        bid_daiAmount = exchange_contract.functions.getEthToTokenInputPrice(ETH_AMOUNT).call()
        bid_price = self.context.web3.toWei(bid_daiAmount, 'Ether') / ETH_AMOUNT / ETH_AMOUNT

        offer_daiAmount = exchange_contract.functions.getTokenToEthOutputPrice(ETH_AMOUNT).call()
        offer_price = self.context.web3.toWei(offer_daiAmount, 'Ether') / ETH_AMOUNT / ETH_AMOUNT

        return {'value': (bid_price, offer_price, bid_daiAmount, offer_daiAmount)}
