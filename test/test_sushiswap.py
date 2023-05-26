# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestSushiSwap(CMFTest):
    def test_v2(self):
        default_block_number = 17_001_000

        self.run_model('sushiswap.get-factory', {}, block_number=default_block_number)
        self.run_model('sushiswap.get-pool', {"token0": {"symbol": "USDC"},
                       "token1": {"symbol": "WETH"}}, block_number=default_block_number)
        self.run_model('sushiswap.get-pools', {"symbol": "WETH"}, block_number=default_block_number)
        self.run_model('sushiswap.get-pools-ledger', {"symbol": "WETH"}, block_number=default_block_number)
        self.run_model('sushiswap.get-pools-tokens',
                       {"tokens": [{"symbol": "WETH"}, {"symbol": "USDC"}]}, block_number=default_block_number)
        self.run_model('sushiswap.get-ring0-ref-price', {}, block_number=default_block_number)
        self.run_model('sushiswap.get-pool-info-token-price', {"symbol": "USDC"}, block_number=default_block_number)

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

        self.run_model('uniswap-v2.get-pool-info',
                       {"address": "0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"})

        self.run_model('sushiswap.get-pool-info-token-price',
                       {"address": "0x853d955acef822db058eb8505911ed77f175b99e"}, block_number=15048685)
        self.run_model('sushiswap.get-pool-info-token-price',
                       {"address": "0x853d955acef822db058eb8505911ed77f175b99e"}, block_number=14048685)

    def test_pools_token(self):
        link_pools = self.run_model_with_output("sushiswap.get-pools", {"symbol": "LINK"})
        link_pools_alt = self.run_model_with_output("sushiswap.get-pools-tokens", {"tokens": [{"symbol": "LINK"}]})

        self.assertEqual({x['address'] for x in link_pools['output']['contracts']},
                         {x['address'] for x in link_pools_alt['output']['contracts']})

        mkr_pools = self.run_model_with_output("sushiswap.get-pools", {"symbol": "MKR"})
        mkr_pools_alt = self.run_model_with_output("sushiswap.get-pools-tokens", {"tokens": [{"symbol": "MKR"}]})

        self.assertEqual({x['address'] for x in mkr_pools['output']['contracts']},
                         {x['address'] for x in mkr_pools_alt['output']['contracts']})

        link_mkr_pools_alt = self.run_model_with_output(
            'sushiswap.get-pools-tokens', {"tokens": [{"symbol": "LINK"},
                                                      {"symbol": "MKR"}]})

        self.assertEqual({x['address'] for x in link_pools['output']['contracts']} | {x['address'] for x in mkr_pools['output']['contracts']},
                         {x['address'] for x in link_mkr_pools_alt['output']['contracts']})

        usdc_pools = self.run_model_with_output("sushiswap.get-pools", {"symbol": "USDC"})
        link_mkr_usdc_pools_alt = self.run_model_with_output(
            'sushiswap.get-pools-tokens', {"tokens": [{"symbol": "LINK"},
                                                      {"symbol": "MKR"},
                                                      {"symbol": "USDC"}]})

        self.assertEqual({x['address'] for x in link_pools['output']['contracts']} |
                         {x['address'] for x in mkr_pools['output']['contracts']} |
                         {x['address'] for x in usdc_pools['output']['contracts']},
                         {x['address'] for x in link_mkr_usdc_pools_alt['output']['contracts']})

        print(
            f'[sushiswap.test_pools_token] '
            f'link_pools: {len(link_pools["output"]["contracts"])} '
            f'mkr_pools: {len(mkr_pools["output"]["contracts"])} '
            f'link_mkr_pools_alt: {len(link_mkr_pools_alt["output"]["contracts"])}')

        # CMK_ADDRESS, sushiswap.get-v2-factory
        cmk_pools = self.run_model_with_output(
            'sushiswap.get-pools', {"address": "0x68CFb82Eacb9f198d508B514d898a403c449533E"})
        cmk_pools_alt = self.run_model_with_output(
            'sushiswap.get-pools-tokens', {"tokens": [{"address": "0x68CFb82Eacb9f198d508B514d898a403c449533E"}]})

        self.assertEqual({x['address'] for x in cmk_pools['output']['contracts']},
                         {x['address'] for x in cmk_pools_alt['output']['contracts']})
