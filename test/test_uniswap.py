# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestUniswapPools(CMFTest):
    def pool_tests(self, model_prefix, default_block_number, chain_id,
                   ring0_token, ring1_token, ring2_token,
                   do_test_ledger=True):
        default_args = {'block_number': default_block_number, 'chain_id': chain_id}

        self.run_model(f'{model_prefix}.get-factory', {}, **default_args)

        if model_prefix.endswith('-v2'):
            self.run_model(f'{model_prefix}.get-pool-by-pair',
                           {"token0": {"symbol": ring0_token}, "token1": {"symbol": ring1_token}},
                           **default_args)

        if model_prefix.endswith('-v3'):
            self.run_model(f'{model_prefix}.get-pools-by-pair',
                           {"token0": {"symbol": ring0_token}, "token1": {"symbol": ring1_token}},
                           **default_args)

        for token in [ring0_token, ring1_token, ring2_token]:
            self.run_model(f'{model_prefix}.get-pools', {"symbol": token},
                           **default_args)
            if do_test_ledger:
                self.run_model(f'{model_prefix}.get-pools-ledger', {"symbol": token},
                               **default_args)

        self.run_model(f'{model_prefix}.get-pools-tokens',
                       {"tokens": [{"symbol": ring0_token}, {"symbol": ring1_token}, {"symbol": ring2_token}]},
                       **default_args)

        self.run_model(f'{model_prefix}.get-ring0-ref-price', {}, **default_args)

        for token in [ring0_token, ring1_token, ring2_token]:
            self.run_model(f'{model_prefix}.get-pool-info-token-price',
                           {"symbol": token}, **default_args)
            self.run_model(f'{model_prefix}.get-weighted-price',
                           {"symbol": token}, **default_args)


class TestUniswap(TestUniswapPools):
    def test(self):
        self.title("Uniswap")

        self.pool_tests('uniswap-v2', 17_001_204, 1, 'USDC', 'WETH', 'MKR')

        self.pool_tests('uniswap-v3', 17_010_204, 1, 'USDC', 'WETH', 'MKR')

        self.pool_tests('uniswap-v3', 43_698_404, 137, 'USDC', 'WMATIC', 'XSGD', do_test_ledger=False)

        self.run_model("uniswap.tokens")
        self.run_model("uniswap.exchange")

        # WETH: 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2
        self.run_model("uniswap.quoter-price-dai",
                       {"address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"})
        self.run_model("uniswap.router")

        self.title("Uniswap V2")
        self.run_model("uniswap-v2.get-weighted-price", {"symbol": "WETH"})
        # uniswap-v2.get-pool-info-token-price
        self.run_model("uniswap-v2.get-weighted-price", {"symbol": "USDT"})
        self.run_model("uniswap-v2.get-weighted-price", {"symbol": "USDC"})
        self.run_model("uniswap-v2.get-weighted-price", {"symbol": "DAI"})
        self.run_model("uniswap-v2.get-weighted-price", {"symbol": "AAVE"})
        # self.run_model("uniswap-v2.get-weighted-price", {"symbol": "MIM"}) # no liquidity
        self.run_model("uniswap-v2.get-weighted-price", {"symbol": "MKR"})
        # 0xD533a949740bb3306d119CC777fa900bA034cd52: Curve DAO Token (CRV)
        self.run_model("uniswap-v2.get-pools",
                       {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"})

        self.title("Uniswap V3")
        # uniswap-v3.get-pool-info, uniswap-v3.get-pool-info-token-price

        self.run_model("uniswap-v3.get-weighted-price-maybe",
                       {"symbol": "WETH"})
        self.run_model("uniswap-v3.get-weighted-price", {"symbol": "WETH"})
        self.run_model("uniswap-v3.get-weighted-price", {"symbol": "USDT"})
        self.run_model("uniswap-v3.get-weighted-price", {"symbol": "USDC"})
        self.run_model("uniswap-v3.get-weighted-price", {"symbol": "DAI"})
        self.run_model("uniswap-v3.get-weighted-price", {"symbol": "MIM"})
        self.run_model("uniswap-v3.get-weighted-price",
                       {"symbol": "AAVE"})  # uniswap-v3.get-pool-info

        self.run_model("uniswap-v3.get-weighted-price",
                       {"symbol": "MKR"})  # uniswap-v3.get-pool-info

        # No liquidity
        # self.run_model("uniswap-v3.get-weighted-price", {"symbol": "CMK"})  # uniswap-v3.get-pool-info

        # WETH/CMK pool: 0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3
        self.run_model("uniswap-v3.get-pool-info",
                       {"address": "0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3"})
        self.run_model("uniswap-v3.get-pool-info-token-price",
                       {"symbol": "MKR"})

        self.run_model("uniswap-v2.get-pool-info-token-price",
                       {"address": "0x853d955acef822db058eb8505911ed77f175b99e"}, block_number=15048685)
        self.run_model("uniswap-v2.get-pool-info-token-price",
                       {"address": "0x853d955acef822db058eb8505911ed77f175b99e"}, block_number=14048685)

        # liquidity
        self.run_model("uniswap-v3.get-liquidity-by-ticks",
                       {"address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", "min_tick": 202000, "max_tick": 203000},
                       block_number=15276693)

        current_tick = 202180

        self.run_model("uniswap-v3.get-amount-in-ticks",
                       {"address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                        "min_tick": current_tick-1000,
                        "max_tick": current_tick+1000},
                       block_number=12377278)

        self.run_model("uniswap-v2.get-pool-price-info",
                       {"address": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                        "price_slug": "uniswap-v2.get-weighted-price",
                        "ref_price_slug": "uniswap-v2.get-ring0-ref-price",
                        "protocol": "uniswap-v2"})

        self.run_model("uniswap-v2.get-pool-price-info",
                       {"address": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                        "price_slug": "uniswap-v2.get-weighted-price",
                        "ref_price_slug": None,
                        "protocol": "uniswap-v2"})

        # pool Swap events
        # if "--api_url=http://localhost:8700" in self.post_flag:
        self.run_model("dex.pool-volume-block-range",
                       {"address": "0x5777d92f208679DB4b9778590Fa3CAB3aC9e2168"})
        self.run_model("dex.pool-volume-block-range",
                       {"address": "0x60594a405d53811d3BC4766596EFD80fd545A270"})

    def test_lp(self):
        self.run_model("uniswap-v2.lp-pos",
                       {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc", "lp_balance": 10000})

        self.run_model("uniswap-v2.lp-fee-history",
                       {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                           "lp": "0x76E2E2D4d655b83545D4c50D9521F5bc63bC5329"},
                       block_number=15_936_945)

        self.run_model("uniswap-v2.lp-fee-history",
                       {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                           "lp": "0x109B3C39d675A2FF16354E116d080B94d238a7c9"},
                       block_number=15_936_945)

        self.run_model("uniswap-v2.lp-fee",
                       {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                           "lp": "0x76E2E2D4d655b83545D4c50D9521F5bc63bC5329"},
                       block_number=15_933_378)

        self.run_model("uniswap-v2.lp-fee",
                       {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                           "lp": "0x109B3C39d675A2FF16354E116d080B94d238a7c9"},
                       block_number=15_936_945)

        # 5 deposits and 1 withdraw: 15977444 - 16094145
        self.run_model("uniswap-v2.lp-fee",
                       {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                           "lp": "0x18196A32F99bD5feeAfd6bD6b55a63A0EeEf23a6"},
                       block_number=16_495_182)

        # 19      15933378 332  0x76e2e2d4d655b83545d4c50d9521f5bc63bc5329  0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc - 73345863221727   43423.909024   35.432141 - 5366.999992 - 4.379253   48697.181460   39.734917      93.727556    0.076478
        # 20      15936945 - 1  0x76e2e2d4d655b83545d4c50d9521f5bc63bc5329  0x76e2e2d4d655b83545d4c50d9521f5bc63bc5329                  0   42487.140465   36.303070      0.000000    0.000000   42434.611431   36.258187      52.529034    0.044883

        self.run_model("uniswap-v2.lp", {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                       "lp": "0x2344f131b07e6afd943b0901c55898573f0d1561"})

        self.run_model("uniswap-v3.lp", {"lp": "0x297e12154bde98e96d475fc3a554797f7a6139d0"}, block_number=15931588)
        self.run_model("uniswap-v3.lp", {"lp": "0xa57Bd00134B2850B2a1c55860c9e9ea100fDd6CF"}, block_number=15931588)
        self.run_model("uniswap-v3.lp", {"lp": "0x109B3C39d675A2FF16354E116d080B94d238a7c9"}, block_number=15931588)
        self.run_model("uniswap-v3.id", {"id": 355427}, block_number=15931588)
        self.run_model("uniswap-v3.id", {"id": 355415}, block_number=15931588)

        self.run_model('uniswap-v3.get-ring0-ref-price', {})

    def test_v2_lp(self):
        # credmark-dev run uniswap-v2.lp-amount -i '{"address": "0xce84867c3c02b05dc570d0135103d3fb9cc19433"}' -j -b 17153464 --api_url=http://localhost:8700
        # credmark-dev run price.quote -i '{"base": "0xce84867c3c02b05dc570d0135103d3fb9cc19433"}' -j -b 17153464 --api_url=http://localhost:8700
        # credmark-dev run price.cex -i '{"base": "0xce84867c3c02b05dc570d0135103d3fb9cc19433"}' -j -b 17153464 --api_url=http://localhost:8700
        # credmark-dev run price.dex -i '{"base": "0xce84867c3c02b05dc570d0135103d3fb9cc19433"}' -j -b 17153464 --api_url=http://localhost:8700

        # credmark-dev run uniswap-v2.lp-amount -i '{"address": "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"}' -j -b 17153464 --api_url=http://localhost:8700
        # credmark-dev run price.quote -i '{"base": "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"}' -j -b 17153464 --api_url=http://localhost:8700
        # credmark-dev run price.cex -i '{"base": "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"}' -j -b 17153464 --api_url=http://localhost:8700
        # credmark-dev run price.dex -i '{"base": "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"}' -j -b 17153464 --api_url=http://localhost:8700

        # https://etherscan.io/tx/0x990a25a466f4df31bf70afcf3664149fbae23bbfd66653d1e1202a3c97d75c85
        # pool: 0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc
        # block: 17136921

        pool_address = [
            '0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc',  # USDC - WETH
            '0xce84867c3c02b05dc570d0135103d3fb9cc19433',  # SUSHI - WETH
            '0xdc2b82bc1106c9c5286e59344896fb0ceb932f53',  # WETH - RGT
        ]

        for pool_addr in pool_address:
            self.run_model("uniswap-v2.lp-amount", {"address": pool_addr}, block_number=17136921)

            self.run_model("price.dex", {"base": pool_addr}, block_number=17136921)

    def test_pools_tokens(self):
        link_pools = self.run_model_with_output("uniswap-v3.get-pools", {"symbol": "LINK"})
        link_pools_alt = self.run_model_with_output("uniswap-v3.get-pools-tokens", {"tokens": [{"symbol": "LINK"}]})

        self.assertEqual({x['address'] for x in link_pools['output']['contracts']},
                         {x['address'] for x in link_pools_alt['output']['contracts']})

        mkr_pools = self.run_model_with_output("uniswap-v3.get-pools", {"symbol": "MKR"})
        mkr_pools_alt = self.run_model_with_output("uniswap-v3.get-pools-tokens", {"tokens": [{"symbol": "MKR"}]})

        self.assertEqual({x['address'] for x in mkr_pools['output']['contracts']},
                         {x['address'] for x in mkr_pools_alt['output']['contracts']})

        link_mkr_pools_alt = self.run_model_with_output(
            'uniswap-v3.get-pools-tokens', {"tokens": [{"symbol": "LINK"},
                                                       {"symbol": "MKR"}]})

        self.assertEqual({x['address'] for x in link_pools['output']['contracts']} | {x['address'] for x in mkr_pools['output']['contracts']},
                         {x['address'] for x in link_mkr_pools_alt['output']['contracts']})

    def test_pools_tokens_v2(self):
        link_pools = self.run_model_with_output("uniswap-v2.get-pools", {"symbol": "LINK"})
        link_pools_alt = self.run_model_with_output("uniswap-v2.get-pools-tokens", {"tokens": [{"symbol": "LINK"}]})

        self.assertEqual({x['address'] for x in link_pools['output']['contracts']},
                         {x['address'] for x in link_pools_alt['output']['contracts']})

        mkr_pools = self.run_model_with_output("uniswap-v2.get-pools", {"symbol": "MKR"})
        mkr_pools_alt = self.run_model_with_output("uniswap-v2.get-pools-tokens", {"tokens": [{"symbol": "MKR"}]})

        self.assertEqual({x['address'] for x in mkr_pools['output']['contracts']},
                         {x['address'] for x in mkr_pools_alt['output']['contracts']})

        link_mkr_pools_alt = self.run_model_with_output(
            'uniswap-v2.get-pools-tokens', {"tokens": [{"symbol": "LINK"},
                                                       {"symbol": "MKR"}]})

        self.assertEqual({x['address'] for x in link_pools['output']['contracts']} | {x['address'] for x in mkr_pools['output']['contracts']},
                         {x['address'] for x in link_mkr_pools_alt['output']['contracts']})
