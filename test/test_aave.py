# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestAAVE(CMFTest):
    def test(self):
        self.title("Aave V2")

        self.run_model("aave-v2.get-oracle-price", {"symbol": "AAVE"})
        self.run_model("aave-v2.get-price-oracle")
        self.run_model("aave-v2.get-lending-pool-providers-from-registry")

        # aave-v2.get-lending-pool, aave-v2.get-lending-pool-provider
        self.run_model("aave-v2.token-asset",
                       {"address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"})

        self.run_model("aave-v2.token-asset", {"symbol": "USDC"})
        self.run_model("aave-v2.token-asset", {"symbol": "DAI"})
        self.run_model("aave-v2.lending-pool-assets",
                       {})  # aave-v2.token-asset

        # 0xE41d2489571d322189246DaFA5ebDe1F4699F498: ZRX
        self.run_model("aave-v2.token-liability",
                       {"address": "0xE41d2489571d322189246DaFA5ebDe1F4699F498"})
        self.run_model("aave-v2.token-liability", {"symbol": "USDC"})
        self.run_model("aave-v2.overall-liabilities-portfolio",
                       {})  # aave-v2.token-liability
        # 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48: USDC

        self.run_model("aave-v2.lending-pool-assets",
                       {}, block_number=12770589)

        self.run_model("aave-v2.lending-pool-assets-portfolio",
                       {}, block_number=12770589)

        self.run_model("aave-v2.account-info",
                       {"address": "0x4a49985b14bd0ce42c25efde5d8c379a48ab02f3"}, block_number=16325819)

    def test_reserve(self):
        self.run_model("aave-v2.reserve-config",
                       {"symbol": "AAVE"}, block_number=16462000)
        self.run_model("aave-v2.reserve-config",
                       {"symbol": "CRV"}, block_number=16462000)
        self.run_model("aave-v2.reserve-config",
                       {"symbol": "LINK"}, block_number=16462000)

    def test_account(self):
        # WBTC as collateral
        self.run_model("aave-v2.account-info-reserve",
                       {"address": "0x4a49985b14bd0ce42c25efde5d8c379a48ab02f3",
                        "reserve": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"},
                       block_number=16694809)

        self.run_model("aave-v2.account-info",
                       {"address": "0x4a49985b14bd0ce42c25efde5d8c379a48ab02f3"}, block_number=16325819)

        self.run_model("aave-v2.account-summary",
                       {"address": "0x4a49985b14bd0ce42c25efde5d8c379a48ab02f3"}, block_number=16325819)

        self.run_model("aave-v2.account-summary",
                       {"address": "0x57E04786E231Af3343562C062E0d058F25daCE9E"}, block_number=16040000)

        self.run_model("aave-v2.account-summary-historical",
                       {"address": "0x57E04786E231Af3343562C062E0d058F25daCE9E",
                           "window": "10 days", "interval": "1 days"},
                       block_number=16040000)

    def test_aave_reward(self):
        self.run_model("aave-v2.get-lp-reward",
                       {"address": "0x5a7ED8CB7360db852E8AB5B10D10Abd806dB510D"},
                       block_number=13904702)

        self.run_model("aave-v2.get-staking-reward",
                       {"address": "0x5a7ED8CB7360db852E8AB5B10D10Abd806dB510D"},
                       block_number=13904702)
