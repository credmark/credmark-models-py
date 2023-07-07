# pylint:disable=locally-disabled,line-too-long

from test_uniswap import TestUniswapPools


class TestQuickSwap(TestUniswapPools):
    def test_v2(self):
        self.pool_tests('quickswap-v2', 43_715_100, 137, 'USDC', 'WMATIC', 'GHST', do_test_ledger=False)

    def test_v3(self):
        self.pool_tests('quickswap-v3', 43_715_100, 137, 'USDC', 'WETH', 'LINK', do_test_ledger=False)
