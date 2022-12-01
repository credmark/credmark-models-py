# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestDashboard(CMFTest):
    SUSHI_POOLS = ['0x6a091a3406E0073C3CD6340122143009aDac0EDa',
                   '0x397ff1542f962076d0bfe58ea045ffa2d347aca0',
                   '0xceff51756c56ceffca006cd410b03ffc46dd3a58',
                   '0xe12af1218b4e9272e9628d7c7dc6354d137d024e',
                   '0xd4e7a6e2d03e4e48dfc27dd3f46df1c176647e38',
                   '0x06da0fd433c1a5d7a4faa01111c044910a184553',
                   '0x055475920a8c93cffb64d039a8205f7acc7722d3',
                   '0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f',
                   '0xdB06a76733528761Eda47d356647297bC35a98BD',
                   '0x795065dcc9f64b5614c407a6efdc400da6221fb0']

    UNIV2_POOLS = ['0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc',
                   '0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc',
                   '0x21b8065d10f73ee2e260e5b47d3344d3ced7596e',
                   '0x9928e4046d7c6513326ccea028cd3e7a91c7590a',
                   '0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852',
                   '0xe1573b9d29e2183b1af0e743dc2754979a40d237',
                   '0xae461ca67b15dc8dc81ce7615e0320da1a9ab8d5',
                   '0xccb63225a7b19dcf66717e4d40c9a72b39331d61',
                   '0x3041cbd36888becc7bbcbc0045e3b1f144466f5f',
                   '0x9fae36a18ef8ac2b43186ade5e2b07403dc742b1',
                   '0x61b62c5d56ccd158a38367ef2f539668a06356ab',
                   '0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58',
                   '0x3da1313ae46132a397d90d95b1424a9a7e3e0fce']

    UNIV3_POOLS = ['0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8',
                   '0xcbcdf9626bc03e24f779434178a73a0b4bad62ed',
                   '0xc63b0708e2f7e69cb8a1df0e1389a98c35a76d52',
                   '0x4e68ccd3e89f51c3074ca5072bbac773960dfa36',
                   '0x97e7d56a0408570ba1a7852de36350f7713906ec',
                   '0x99ac8ca7087fa4a2a1fb6357269965a2014abc35',
                   '0x5777d92f208679DB4b9778590Fa3CAB3aC9e2168',
                   '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640',
                   '0x3416cf6c708da44db2624d63ea0aaef7113527c6',
                   '0x7379e81228514a1d2a6cf7559203998e20598346',
                   '0x4674abc5796e1334B5075326b39B748bee9EaA34']

    CURVE_POOLS = ['0x961226b64ad373275130234145b96d100dc0b655',
                   '0x8301AE4fc9c624d1D396cbDAa1ed877821D7C511',
                   '0x43b4FdFD4Ff969587185cDB6f0BD875c5Fc83f8c',
                   '0xd658A338613198204DCa1143Ac3F01A722b5d94A',
                   '0xDC24316b9AE028F1497c275EB9192a3Ea0f67022',
                   '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7',
                   '0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B',
                   '0xCEAF7747579696A2F0bb206a14210e3c9e6fB269',
                   '0xD51a44d3FaE010294C616388b506AcdA1bfAAE46',
                   '0x5a6A4D54456819380173272A5E8E9B9904BdF41B',
                   '0x93054188d876f558f4a66B2EF1d97d16eDf0895B',
                   '0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF',
                   '0x9D0464996170c6B9e75eED71c68B99dDEDf279e8',
                   '0x828b154032950C8ff7CF8085D841723Db2696056']

    def test_volume_historical(self):
        self.title('Curve TVL/Volume - Historical')

        self.run_model('dex.pool-volume-historical', {"pool_info_model": "curve-fi.pool-tvl", "interval": 7200,
                       "count": 2, "address": "0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B"}, block_number=14048685)
        self.run_model('dex.pool-volume-historical', {"pool_info_model": "curve-fi.pool-tvl", "interval": 7200,
                       "count": 2, "address": "0x5a6A4D54456819380173272A5E8E9B9904BdF41B"}, block_number=15048685)
        self.run_model('dex.pool-volume-historical', {"pool_info_model": "uniswap-v2.pool-tvl", "interval": 7200,
                       "count": 2, "address": "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f"}, block_number=14048685)

    def test_lp_var(self):
        block_number = 14830357
        self.title('Longer Test for LP VaR')

        self.run_model('finance.var-dex-lp',
                       {"pool": {"address": "0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58"},
                        "window": "23 days", "interval": 10, "confidence": 0.01, "lower_range": 0.01, "upper_range": 0.01},
                       block_number=block_number)

        self.run_model('finance.var-dex-lp',
                       {"pool": {"address": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"},
                        "window": "90 days", "interval": 10, "confidence": 0.01, "lower_range": 0.01, "upper_range": 0.01},
                       block_number=15263892)

        self.run_model('finance.var-dex-lp',
                       {"pool": {"address": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8"},
                        "window": "90 days", "interval": 10, "confidence": 0.01, "lower_range": 0.01, "upper_range": 0.01},
                       block_number=15263892)

        for range_of_pool in [0.01, 0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0]:
            print(f'LP VaR Range: {range_of_pool}')
            self.run_model('finance.var-dex-lp',
                           {"pool": {"address": "0xcbcdf9626bc03e24f779434178a73a0b4bad62ed"},
                            "window": "23 days", "interval": 10, "confidence": 0.01, "lower_range": range_of_pool, "upper_range": range_of_pool},
                           block_number=block_number)

    def test_dex_pool_volume(self) -> None:
        self.run_model('dex.pool-volume-historical', {"pool_info_model": "uniswap-v2.pool-tvl", "interval": 7200,
                       "count": 2, "address": "0x9928e4046d7c6513326ccea028cd3e7a91c7590a"})

        # credmark-dev run dex.pool-volume -i '{"pool_info_model": "uniswap-v2.pool-tvl", "interval": 7200,"count": 2, "address": "0x9928e4046d7c6513326ccea028cd3e7a91c7590a"}' --api_url=http://localhost:8700 -j
        self.run_model('dex.pool-volume', {"pool_info_model": "uniswap-v2.pool-tvl", "interval": 7200,
                       "count": 2, "address": "0x9928e4046d7c6513326ccea028cd3e7a91c7590a"})

        # credmark-dev run pool.dex-db-latest -i '{"address": "0x9928e4046d7c6513326ccea028cd3e7a91c7590a"}' --api_url=http://localhost:8700 -j
        # credmark-dev run pool.dex-db-latest -i '{"address": "0x9fae36a18ef8ac2b43186ade5e2b07403dc742b1"}' --api_url=http://localhost:8700 -j
        self.run_model('pool.dex-db-latest', {"address": "0x9928e4046d7c6513326ccea028cd3e7a91c7590a"})

        self.run_model('dex.pool-volume-historical', {"pool_info_model": "uniswap-v2.pool-tvl", "interval": 7200,
                       "count": 2, "address": "0x795065dcc9f64b5614c407a6efdc400da6221fb0"})

        self.run_model('dex.pool-volume', {"pool_info_model": "uniswap-v2.pool-tvl", "interval": 7200,
                       "count": 2, "address": "0x795065dcc9f64b5614c407a6efdc400da6221fb0"})

        self.run_model('pool.dex-db-latest', {"address": "0x795065dcc9f64b5614c407a6efdc400da6221fb0"})


def run_test_uni(self, pool_n, pool, test_volume):
    # Uniswap V2: 0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58
    # Uniswap V3: 0xcbcdf9626bc03e24f779434178a73a0b4bad62ed
    # Uniswap V3: 0x4674abc5796e1334B5075326b39B748bee9EaA34

    # run_model_historical("finance.var-dex-lp", model_input={"pool": {"address":"0x4674abc5796e1334B5075326b39B748bee9EaA34"}, "window":"280 days", "interval":10, "confidence": 0.01, "lower_range": 0.01, "upper_range":0.01}, window="120 days")
    # models.finance.var_dex_lp({"pool": {"address":"0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58"}, "window":"280 days", "interval":10, "confidence": 0.01, "lower_range": 0.01, "upper_range":0.01}, block_number=14830357)

    # 13909787 - datetime.datetime(2021, 12, 31, 0, 0, tzinfo=datetime.timezone.utc)
    # 14830357 - datetime.datetime(2022, 5, 23, 15, 26, 40, tzinfo=datetime.timezone.utc)

    block_number = 14830357
    self.title(f'Pool TVL/Volume/VaR - Uni/Sushi - {pool_n}')

    # for pool in $univ3_pools; do
    # for pool in $sushi_pools $univ2_pools; do
    self.run_model('uniswap-v2.get-pool-info', {"address": pool}, block_number=block_number)
    self.run_model('uniswap-v2.pool-tvl', {"address": pool}, block_number=block_number)

    if test_volume:
        self.run_model('dex.pool-volume-historical',
                       {"pool_info_model": "uniswap-v2.pool-tvl", "interval": 7200, "count": 2, "address": pool}, block_number=block_number)

        self.run_model('dex.pool-volume',
                       {"pool_info_model": "uniswap-v2.pool-tvl", "interval": 7200, "address": pool},
                       block_number=block_number)

    self.run_model('finance.var-dex-lp',
                   {"pool": {"address": pool}, "window": "7 days", "interval": 1,
                    "confidence": 0.01, "lower_range": 0.01, "upper_range": 0.01},
                   block_number=block_number)


def run_test_curve(self, pool_n, pool, test_volume):
    block_number = 14830357
    self.title(f'Pool TVL/Volume/VaR - Curve - {pool_n}')

    # curve_pool_info_tvl = curve-fi.pool-info, chainlink.price-by-registry

    self.run_model('curve-fi.pool-tvl',
                   {"address": pool},
                   block_number=block_number)

    if test_volume:
        self.run_model('dex.pool-volume-historical',
                       {"pool_info_model": "curve-fi.pool-tvl", "interval": 7200, "count": 2, "address": pool},
                       block_number=block_number)

    self.run_model('dex.pool-volume',
                   {"pool_info_model": "curve-fi.pool-tvl", "interval": 7200, "address": pool},
                   block_number=block_number)
    self.run_model('historical.run-model',
                   {"model_slug": "curve-fi.pool-tvl", "model_input": {"address": pool},
                    "window": "3 days", "interval": "1 day"},
                   block_number=block_number)


for n, addr in enumerate(TestDashboard.UNIV2_POOLS):
    setattr(TestDashboard,
            f'test_univ2_{n+1}',
            lambda self, pool_n=n, pool=addr: run_test_uni(self, pool_n, pool, True))

for n, addr in enumerate(TestDashboard.UNIV3_POOLS):
    setattr(TestDashboard,
            f'test_univ3_{n+1}',
            lambda self, pool_n=n, pool=addr: run_test_uni(self, pool_n, pool, True))

for n, addr in enumerate(TestDashboard.SUSHI_POOLS):
    setattr(TestDashboard,
            f'test_sushi_{n+1}',
            lambda self, pool_n=n, pool=addr: run_test_uni(self, pool_n, pool, True))

for n, addr in enumerate(TestDashboard.CURVE_POOLS):
    setattr(TestDashboard,
            f'test_curve_{n+1}',
            lambda self, pool_n=n, pool=addr: run_test_curve(self, pool_n, pool, pool_n < 4))
