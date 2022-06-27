# pylint:disable=locally-disabled,line-too-long

from cmk_test import CMKTest


class TestSushiSwap(CMKTest):
    def test(self):
        self.title('SushiSwap')

        self.run_model('sushiswap.get-weighted-price', {"symbol": "USDC"}) # sushiswap.get-pool-info-token-price, uniswap-v2.get-price-pool-info
        self.run_model('sushiswap.get-weighted-price', {"symbol": "AAVE"})
        self.run_model('sushiswap.get-weighted-price', {"symbol": "DAI"})
        self.run_model('sushiswap.get-weighted-price', {"symbol": "WETH"})
        self.run_model('sushiswap.get-weighted-price', {"symbol": "MKR"})
        self.run_model('sushiswap.all-pools', {})
        self.run_model('sushiswap.get-pool', {"token0":{"symbol":"DAI"}, "token1":{"symbol":"WETH"}})
        self.run_model('sushiswap.get-pools', {"address":"0x68CFb82Eacb9f198d508B514d898a403c449533E"}) # CMK_ADDRESS, sushiswap.get-v2-factory
        self.run_model('uniswap-v2.get-pool-info', {"address":"0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"})
