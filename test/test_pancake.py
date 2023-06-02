# pylint:disable=locally-disabled,line-too-long

from test_uniswap import TestUniswapPools


class TestPancakeSwap(TestUniswapPools):
    def test_v2(self):
        default_block_number = 17_001_000
        model_prefix = 'pancakeswap-v2'
        self.v2_pools(model_prefix, default_block_number)

    def test_v2_other_chain(self):
        pass
