# pylint:disable=locally-disabled,line-too-long

from cmk_test import CMKTest


class TestUniswap(CMKTest):
    def test(self):
        self.title('Uniswap')

        self.run_model('uniswap.tokens', {})
        self.run_model('uniswap.exchange', {})
        # WETH: 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2
        self.run_model('uniswap.quoter-price-dai', {"address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"})
        self.run_model('uniswap.router', {})

        self.title('Uniswap V2')
        self.run_model('uniswap-v2.get-weighted-price', {"symbol": "USDC"})  # uniswap-v2.get-pool-info-token-price
        self.run_model('uniswap-v2.get-weighted-price', {"symbol": "AAVE"})
        self.run_model('uniswap-v2.get-weighted-price', {"symbol": "DAI"})
        self.run_model('uniswap-v2.get-weighted-price', {"symbol": "WETH"})
        self.run_model('uniswap-v2.get-weighted-price', {"symbol": "MKR"})
        # 0xD533a949740bb3306d119CC777fa900bA034cd52: Curve DAO Token (CRV)
        self.run_model('uniswap-v2.get-pools', {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"})

        self.title('Uniswap V3')
        # uniswap-v3.get-pool-info, uniswap-v3.get-pool-info-token-price
        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "USDC"})
        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "AAVE"})  # uniswap-v3.get-pool-info
        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "DAI"})  # uniswap-v3.get-pool-info
        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "WETH"})  # uniswap-v3.get-pool-info
        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "MKR"})  # uniswap-v3.get-pool-info
        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "CMK"})  # uniswap-v3.get-pool-info
        self.run_model('uniswap-v3.get-pools', {"symbol": "MKR"})
        # WETH/CMK pool: 0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3
        self.run_model('uniswap-v3.get-pool-info', {"address": "0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3"})
