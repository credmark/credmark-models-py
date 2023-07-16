# pylint:disable=locally-disabled,line-too-long

from test_uniswap import TestUniswapPools


class TestPancakeSwap(TestUniswapPools):
    def test_v2(self):
        self.pool_tests('pancakeswap-v2', 17_001_205, 1, 'USDC', 'WETH', 'STG')

    def test_v3(self):
        self.pool_tests('pancakeswap-v3', 17_001_205, 1, 'USDC', 'WETH', 'STG')

    def test_v2_bsc(self):
        self.pool_tests('pancakeswap-v2', 28_869_137, 56, 'BUSD',
                        'WBNB', 'STA', do_test_ledger=False)

    def test_v3_bsc(self):
        self.pool_tests('pancakeswap-v3', 28_869_137, 56, 'BUSD',
                        'WBNB', 'Cake', do_test_ledger=False)
