# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestPancakeSwap(CMFTest):
    def test_v2(self):
        default_block_number = 17_001_000

        self.run_model('pancakeswap-v2.get-factory', {}, block_number=default_block_number)
        self.run_model('pancakeswap-v2.get-pool', {"token0": {"symbol": "USDC"},
                       "token1": {"symbol": "WETH"}}, block_number=default_block_number)
        self.run_model('pancakeswap-v2.get-pools', {"symbol": "WETH"}, block_number=default_block_number)
        self.run_model('pancakeswap-v2.get-pools-ledger', {"symbol": "WETH"}, block_number=default_block_number)
        self.run_model('pancakeswap-v2.get-pools-tokens',
                       {"tokens": [{"symbol": "WETH"}, {"symbol": "USDC"}]}, block_number=default_block_number)
        self.run_model('pancakeswap-v2.get-ring0-ref-price', {}, block_number=default_block_number)
        self.run_model('pancakeswap-v2.get-pool-info-token-price',
                       {"symbol": "USDC"}, block_number=default_block_number)

    def test_v2_other_chain(self):
        pass
