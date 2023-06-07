# pylint:disable=locally-disabled,line-too-long

from test_uniswap import TestUniswapPools


class TestPancakeSwap(TestUniswapPools):
    def test_v2(self):
        default_block_number = 17_001_000
        self.pool_tests('pancakeswap-v2', default_block_number, 1, 'USDC', 'WETH', 'STG')

    def test_v3(self):
        default_block_number = 17_001_000
        self.pool_tests('pancakeswap-v3', default_block_number, 1, 'USDC', 'WETH', 'STG')

    def test_v2_bsc(self):
        self.pool_tests('pancakeswap-v2', 28_868_132, 56, 'BUSD', 'WBNB', 'STA', do_test_ledger=False)

    def test_v3_bsc(self):
        self.pool_tests('pancakeswap-v3', 28_868_132, 56, 'BUSD', 'WBNB', 'Cake', do_test_ledger=False)
