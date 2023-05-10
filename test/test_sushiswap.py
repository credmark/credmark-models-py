# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestSushiSwap(CMFTest):
    def test(self):
        self.title('SushiSwap')

        # sushiswap.get-pool-info-token-price, uniswap-v2.get-pool-price-info
        self.run_model('sushiswap.get-weighted-price', {"symbol": "WETH"})
        self.run_model('sushiswap.get-weighted-price', {"symbol": "USDC"})
        self.run_model('sushiswap.get-weighted-price', {"symbol": "USDT"})
        self.run_model('sushiswap.get-weighted-price', {"symbol": "DAI"})
        self.run_model('sushiswap.get-weighted-price', {"symbol": "AAVE"})
        self.run_model('sushiswap.get-weighted-price', {"symbol": "MKR"})
        self.run_model('sushiswap.get-weighted-price', {"symbol": "CMK"})

        self.run_model('sushiswap.all-pools')
        self.run_model('sushiswap.get-pool',
                       {"token0": {"symbol": "DAI"}, "token1": {"symbol": "WETH"}})
        # CMK_ADDRESS, sushiswap.get-v2-factory
        self.run_model('sushiswap.get-pools',
                       {"address": "0x68CFb82Eacb9f198d508B514d898a403c449533E"})
        self.run_model('uniswap-v2.get-pool-info',
                       {"address": "0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"})

        self.run_model('sushiswap.get-pool-info-token-price',
                       {"address": "0x853d955acef822db058eb8505911ed77f175b99e"}, block_number=15048685)
        self.run_model('sushiswap.get-pool-info-token-price',
                       {"address": "0x853d955acef822db058eb8505911ed77f175b99e"}, block_number=14048685)
