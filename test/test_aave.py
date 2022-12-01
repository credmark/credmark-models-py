# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestAAVE(CMFTest):
    def test(self):
        self.title('Aave V2')

        self.run_model('aave-v2.get-oracle-price', {"symbol": "AAVE"})
        self.run_model('aave-v2.get-price-oracle', {})
        self.run_model('aave-v2.get-lending-pool-providers-from-registry', {})

        # aave-v2.get-lending-pool, aave-v2.get-lending-pool-provider
        self.run_model('aave-v2.token-asset', {"address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"})

        self.run_model('aave-v2.token-asset', {"symbol": "USDC"})
        self.run_model('aave-v2.token-asset', {"symbol": "DAI"})
        self.run_model('aave-v2.lending-pool-assets', {})  # aave-v2.token-asset

        # 0xE41d2489571d322189246DaFA5ebDe1F4699F498: ZRX
        self.run_model('aave-v2.token-liability', {"address": "0xE41d2489571d322189246DaFA5ebDe1F4699F498"})
        self.run_model('aave-v2.token-liability', {"symbol": "USDC"})
        self.run_model('aave-v2.overall-liabilities-portfolio', {})  # aave-v2.token-liability
        # 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48: USDC

        self.run_model('aave-v2.lending-pool-assets', {}, block_number=12770589)

        self.run_model('aave-v2.lending-pool-assets-portfolio', {}, block_number=12770589)
