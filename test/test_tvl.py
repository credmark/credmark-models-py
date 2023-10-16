# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestTVL(CMFTest):
    def test(self):
        block_number = 14830357
        self.title('TVL')

        # curve_pool_info_tvl=curve-fi.pool-info,price.quote,chainlink.price-by-registry

        self.run_model('curve-fi.pool-info',
                       {"address": "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"}, block_number=block_number)
        # ${curve_pool_info_tvl}
        self.run_model('curve-fi.pool-tvl',
                       {"address": "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"}, block_number=block_number)

        curve_pools = ['0xDC24316b9AE028F1497c275EB9192a3Ea0f67022',
                       '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7',
                       '0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B',
                       # '0xCEAF7747579696A2F0bb206a14210e3c9e6fB269',
                       '0xD51a44d3FaE010294C616388b506AcdA1bfAAE46',
                       '0x5a6A4D54456819380173272A5E8E9B9904BdF41B',
                       '0x93054188d876f558f4a66B2EF1d97d16eDf0895B',
                       '0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF',
                       '0x9D0464996170c6B9e75eED71c68B99dDEDf279e8',
                       '0xd658A338613198204DCa1143Ac3F01A722b5d94A']

        for pool_addr in curve_pools:
            self.run_model('curve-fi.pool-tvl', {"address": pool_addr},
                           block_number=block_number)  # ${curve_pool_info_tvl}

        self.title('TVL Historical')

        for pool_addr in curve_pools:
            self.run_model('historical.run-model', {"model_slug": "curve-fi.pool-tvl", "model_input": {
                "address": pool_addr}, "window": "3 days", "interval": "1 day"},
                block_number=block_number)  # ${curve_pool_info_tvl}
