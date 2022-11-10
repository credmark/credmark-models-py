# pylint:disable=locally-disabled,line-too-long

from cmk_test import CMKTest


class TestUniswap(CMKTest):
    def test(self):
        self.title('Uniswap')

        self.run_model('uniswap.tokens', {})
        self.run_model('uniswap.exchange', {})
        # WETH: 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2
        self.run_model('uniswap.quoter-price-dai', {"address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"})
        self.run_model('uniswap.router', {})

        self.title('Uniswap V2')
        self.run_model('uniswap-v2.get-weighted-price', {"symbol": "WETH"})
        self.run_model('uniswap-v2.get-weighted-price', {"symbol": "USDT"})  # uniswap-v2.get-pool-info-token-price
        self.run_model('uniswap-v2.get-weighted-price', {"symbol": "USDC"})
        self.run_model('uniswap-v2.get-weighted-price', {"symbol": "DAI"})
        self.run_model('uniswap-v2.get-weighted-price', {"symbol": "AAVE"})
        # self.run_model('uniswap-v2.get-weighted-price', {"symbol": "MIM"}) # no liquidity
        self.run_model('uniswap-v2.get-weighted-price', {"symbol": "MKR"})
        # 0xD533a949740bb3306d119CC777fa900bA034cd52: Curve DAO Token (CRV)
        self.run_model('uniswap-v2.get-pools', {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"})

        self.title('Uniswap V3')
        # uniswap-v3.get-pool-info, uniswap-v3.get-pool-info-token-price

        self.run_model('uniswap-v3.get-weighted-price-maybe', {"symbol": "WETH"})
        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "WETH"})
        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "USDT"})
        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "USDC"})
        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "DAI"})
        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "MIM"})
        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "AAVE"})  # uniswap-v3.get-pool-info

        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "MKR"})  # uniswap-v3.get-pool-info
        self.run_model('uniswap-v3.get-weighted-price', {"symbol": "CMK"})  # uniswap-v3.get-pool-info
        self.run_model('uniswap-v3.get-pools', {"symbol": "MKR"})
        # WETH/CMK pool: 0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3
        self.run_model('uniswap-v3.get-pool-info', {"address": "0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3"})

        self.run_model('uniswap-v2.get-pool-info-token-price',
                       {"address": "0x853d955acef822db058eb8505911ed77f175b99e"}, block_number=15048685)
        self.run_model('uniswap-v2.get-pool-info-token-price',
                       {"address": "0x853d955acef822db058eb8505911ed77f175b99e"}, block_number=14048685)

        # liquidity
        self.run_model('uniswap-v3.get-liquidity-by-ticks',
                       {"address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", "min_tick": 202000, "max_tick": 203000},
                       block_number=15276693)

        current_tick = 202180

        self.run_model('uniswap-v3.get-amount-in-ticks',
                       {"address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                        "min_tick": current_tick-1000,
                        "max_tick": current_tick+1000},
                       block_number=12377278)

        self.run_model('uniswap-v2.get-pool-price-info',
                       {"address": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                        "price_slug": "uniswap-v2.get-weighted-price"})

        # pool Swap events
        self.run_model('dex.pool-volume-block-range', {"address": "0x5777d92f208679DB4b9778590Fa3CAB3aC9e2168"})
        self.run_model('dex.pool-volume-block-range', {"address": "0x60594a405d53811d3BC4766596EFD80fd545A270"})

        self.run_model('uniswap-v3.get-all-pools', {})

    def test_lp(self):
        self.run_model('uniswap-v2.lp-pos', {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc", "lp_balance": 10000})

        self.run_model('uniswap-v2.lp-fee-history',
                       {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc", "lp": "0x76E2E2D4d655b83545D4c50D9521F5bc63bC5329"}, block_number=15936945)

        self.run_model('uniswap-v2.lp-fee-history',
                       {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc", "lp": "0x109B3C39d675A2FF16354E116d080B94d238a7c9"}, block_number=15936945)

        self.run_model('uniswap-v2.lp-fee',
                       {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc", "lp": "0x76E2E2D4d655b83545D4c50D9521F5bc63bC5329"}, block_number=15933378)

        self.run_model('uniswap-v2.lp-fee',
                       {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc", "lp": "0x109B3C39d675A2FF16354E116d080B94d238a7c9"}, block_number=15936945)

        # 19      15933378        332  0x76e2e2d4d655b83545d4c50d9521f5bc63bc5329  0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc - 73345863221727   43423.909024   35.432141 - 5366.999992 - 4.379253   48697.181460   39.734917      93.727556    0.076478
        # 20      15936945 - 1  0x76e2e2d4d655b83545d4c50d9521f5bc63bc5329  0x76e2e2d4d655b83545d4c50d9521f5bc63bc5329                  0   42487.140465   36.303070      0.000000    0.000000   42434.611431   36.258187      52.529034    0.044883

        self.run_model('uniswap-v2.lp', {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                       "lp": "0x2344f131b07e6afd943b0901c55898573f0d1561"})

        self.run_model('uniswap-v3.lp', {"lp": "0x297e12154bde98e96d475fc3a554797f7a6139d0"}, block_number=15931588)
        self.run_model('uniswap-v3.lp', {"lp": "0xa57Bd00134B2850B2a1c55860c9e9ea100fDd6CF"}, block_number=15931588)
        self.run_model('uniswap-v3.lp', {"lp": "0x109B3C39d675A2FF16354E116d080B94d238a7c9"}, block_number=15931588)
        self.run_model('uniswap-v3.id', {"id": 355427}, block_number=15931588)
        self.run_model('uniswap-v3.id', {"id": 355415}, block_number=15931588)
