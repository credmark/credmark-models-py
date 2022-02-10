from credmark.model import Model

uniswap_quoter_address = '0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6'
uniswap_quoter_abi = '[{"inputs": [{"internalType": "bytes", "name": "path", "type": "bytes"}, {"internalType": "uint256", "name": "amountIn", "type": "uint256"}], "name": "quoteExactInput", "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "tokenIn", "type": "address"}, {"internalType": "address", "name": "tokenOut", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}], "name": "quoteExactInputSingle", "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "bytes", "name": "path", "type": "bytes"}, {"internalType": "uint256", "name": "amountOut", "type": "uint256"}], "name": "quoteExactOutput", "outputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "tokenIn", "type": "address"}, {"internalType": "address", "name": "tokenOut", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "uint256", "name": "amountOut", "type": "uint256"}, {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}], "name": "quoteExactOutputSingle", "outputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"}]'

class UniswapRouterPricePair(Model):
    def run(self, data):
        """
        We should be able to hit the IQuoter Interface to get the quoted price from Uniswap. block_number should be taken care of
        """
        uniswap_quoter = self.context.web3.eth.contract(
            address=self.context.web3.toChecksumAddress(uniswap_quoter_address),
            abi=uniswap_quoter_abi)

        WETH9 = '0xd0A1E359811322d97991E03f863a0C30C2cF029C'
        multiDaiKovan = '0x4F96Fe3b7A6Cf9725f59d353F723c1bDb64CA6Aa'

        tokenIn = WETH9
        tokenOut = multiDaiKovan
        fee = 3000
        sqrtPriceLimitX96 = 0
        daiAmount = 1

        quote = uniswap_quoter.functions.quoteExactOutputSingle(tokenIn,
                                                                tokenOut,
                                                                fee,
                                                                daiAmount,
                                                                sqrtPriceLimitX96).call()

        result = {'value': quote}


class UniswapRouterPriceUsd(Model):
    def run(self, data):
        """
        We should be able to hit the IQuoter Interface to get the quoted price from Uniswap, default to USDC/USDT/DAI and throw out outliers.
        """
        result = {'value': 'not yet implemented'}
