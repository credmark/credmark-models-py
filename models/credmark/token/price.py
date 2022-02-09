from credmark.model import Model


class UniswapRouterPricePair(Model):
    def run(self, data):
        """
        We should be able to hit the IQuoter Interface to get the quoted price from Uniswap. block_number should be taken care of
        """
        result = {'value': 'not yet implemented'}


class UniswapRouterPriceUsd(Model):
    def run(self, data):
        """
        We should be able to hit the IQuoter Interface to get the quoted price from Uniswap, default to USDC/USDT/DAI and throw out outliers.
        """
        result = {'value': 'not yet implemented'}
