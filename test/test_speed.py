# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestSpeed(CMFTest):
    def test(self):
        # 39s
        self.run_model('uniswap-v2.get-pool-info',
                       {"address": "0x6a091a3406E0073C3CD6340122143009aDac0EDa"}, block_number=14823357)

        self.run_model('uniswap-v2.get-pool-info-token-price',
                       {"address": "0x6a091a3406E0073C3CD6340122143009aDac0EDa"}, block_number=14823357)

        self.run_model('uniswap-v3.get-pool-info-token-price',
                       {"symbol": "CMK"}, block_number=14823364)

        self.run_model('price.dex-blended',
                       {"symbol": "CMK"}, block_number=14823364)
