# pylint:disable=locally-disabled,line-too-long

from cmk_test import CMKTest


class TestPrice(CMKTest):
    CEX_ONLY_TOKENS = ['0xfa1a856cfa3409cfa145fa4e20eb270df3eb21ab', ]

    CHAINLINK_TOKENS = ['0xf629cbd94d3791c9250152bd8dfbdf380e2a3b9c',
                        '0xc18360217d8f7ab5e7c516566761ea12ce7f9d72',
                        '0xa0246c9032bc3a600820415ae600c6388619a14d',
                        '0x956f47f50a910163d8bf957cf5846d573e7f87ca',
                        '0xaea46A60368A7bD060eec7DF8CBa43b7EF41Ad85',
                        '0xc770eefad204b5180df6a14ee197d99d808ee52d',
                        '0x853d955acef822db058eb8505911ed77f175b99e',
                        '0x4e15361fd6b4bb609fa63c81a2be19d873717870',
                        '0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9',
                        '0x3432b6a60d23ca0dfca7761b7ab56459d9c964d0',
                        '0x6810e776880c02933d47db1b9fc05908e5386b96',
                        '0xc944e90c64b2c07662a292be6244bdf05cda44a7',
                        '0xde30da39c46104798bb5aa3fe8b9e0e1f348163f',
                        '0x056fd409e1d7a124bd7017459dfea2f387b6d5cd',
                        '0x584bc13c7d411c00c01a62e8019472de68768430',
                        '0x6f259637dcd74c767781e37bc6133cd6a68aa161',
                        '0xdf574c24545e5ffecb9a659c229253d4111d87e1',
                        '0x767fe9edc9e0df98e07454847909b5e959d7ca0e',
                        '0xdd974d5c2e2928dea5f71b9825b8b646686bd200',
                        '0x1ceb5cb57c4d4e2b2433641b95dd330a33185a44',
                        '0x5a98fcbea516cf06857215779fd812ca3bef1b32',
                        '0x514910771af9ca656af840dff83e8264ecf986ca',
                        '0xbbbbca6a901c926f240b89eacb641d8aec7aeafd',
                        '0x5f98805a4e8be255a32880fdec7f6728c6568ba0',
                        '0x0f5d2fb29fb7d3cfee444a200298f468908cc942',
                        '0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0',
                        '0x99d8a9c45b2eca8864373a26d1459e3dff1e17f3',
                        '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2',
                        '0xec67005c4e498ec7f55e092bd1d35cbc47c91892',
                        '0x1776e1f26f98b1a5df9cd347953a26dd3cb46671',
                        '0x967da4048cd07ab37855c090aaf366e4ce1b9f48',
                        '0x64aa3364f17a4d01c6f1751fd97c2bd3d7e7f1d5',
                        '0x75231f58b43240c9718dd58b4967c5114342a86c',
                        '0xd26114cd6ee289accf82350c8d8487fedb8a0c07',
                        '0xd26114cd6ee289accf82350c8d8487fedb8a0c07',
                        '0x8e870d67f660d95d5be530380d0ec0bd388289e1',
                        '0x45804880de22913dafe09f4980848ece6ecbaf78',
                        '0xbc396689893d065f41bc2c6ecbee5e0085233447',
                        '0x03ab458634910aad20ef5f1c8ee96f1d6ac54919',
                        '0xfca59cd816ab1ead66534d82bc21e7515ce441cf',
                        '0x408e41876cccdc0f92210600ef50372656052a38',
                        '0x221657776846890989a759BA2973e427DfF5C9bB',
                        '0x8f8221afbb33998d8584a2b05749ba73c37a938a',
                        '0x607f4c5bb672230e8672085532f7e901544a7375',
                        '0x8762db106b2c2a0bccb3a80d1ed41273552616e8',
                        '0x3845badade8e6dff049820680d1f14bd3903a5d0',
                        '0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce',
                        '0xcc8fa225d80b9c7d42f96e9570156c65d6caaa25',
                        '0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f',
                        '0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f',
                        '0x090185f2135308bad17527004364ebcc2d37e5f6',
                        '0x476c5e26a75bd202a9683ffd34359c0cc15be0ff',
                        '0x0ae055097c6d159879521c384f1d2123d1f195e6',
                        '0x57ab1ec28d129707052df4df418d58a2d46d5f51',
                        '0x6b3595068778dd592e39a122f4f5a5cf09c90fe2',
                        '0x8ce9137d39326ad0cd6491fb5cc0cba0e089b6a9',
                        '0x2e9d63788249371f1dfc918a52f8d799f4a38c94',
                        '0xc7283b66eb1eb5fb86327f08e1b5816b0720212b',
                        '0x0000000000085d4780b73119b644ae5ecd22b376',
                        '0x04fa0d235c4abf4bcf4787af4cf447de572ef828',
                        '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984',
                        '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
                        '0x674c6ad92fd080e4004b2312b45f796a192d27a0',
                        '0xdac17f958d2ee523a2206206994597c13d831ec7',
                        '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599',
                        '0x4691937a7508860f876c9c0a2a617e7d9e945d4b',
                        '0x8798249c2e607446efb7ad49ec89dd1865ff4272',
                        '0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e',
                        '0x25f8087ead173b73d6e8b84329989a8eea16cf73',
                        '0xe41d2489571d322189246dafa5ebde1f4699f498',
                        '0xe41d2489571d322189246dafa5ebde1f4699f498',
                        '0x57ab1ec28d129707052df4df418d58a2d46d5f51',
                        '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
                        '0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB',
                        '0x0000000000000000000000000000000000000348',
                        '0xa1d0E215a23d7030842FC67cE582a6aFa3CCaB83',
                        '0xBe1a001FE942f96Eea22bA08783140B9Dcc09D28',
                        '0x0391D2021f89DC339F60Fff84546EA23E337750f',
                        '0xAE12C5930881c53715B369ceC7606B70d8EB229f',
                        '0xE452E6Ea2dDeB012e20dB73bf5d3863A3Ac8d77a',
                        '0x491604c0FDF08347Dd1fa4Ee062a822A5DD06B5D',
                        '0x111111111117dC0aa78b770fA6A738034120C302',
                        '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9',
                        '0xEd04915c23f00A313a544955524EB7DBD823143d',
                        '0xADE00C28244d5CE17D72E40330B1c318cD12B7c3',
                        '0x8Ab7404063Ec4DBcfd4598215992DC3F8EC853d7',
                        '0x00a8b738E453fFd858a7edf03bcCfe20412f0Eb0',
                        '0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF',
                        '0xa1faa113cbE53436Df28FF0aEe54275c13B40975',
                        '0xfF20817765cB7f73d4bde2e66e067E58D11095C2',
                        '0xd46ba6d942050d489dbd938a2c909a5d5039a161',
                        '0x8290333cef9e6d528dd5618fb97a76f268f3edd4',
                        '0xa117000000f279d81a1d3cc75430faa017fa5a2e',
                        '0x4d224452801aced8b2f0aebe155379bb5d594381',
                        '0xA9B1Eb5908CfC3cdf91F9B8B3a74108598009096',
                        '0x18aAA7115705e8be94bfFEBDE57Af9BFc265B998',
                        '0xbb0e17ef65f82ab018d8edd776e8dd940327b28b',
                        '0x3472a5a71965499acd81997a54bba8d852c6e53d',
                        '0xba100000625a3754423978a60c9317c58a424e3d',
                        '0xba11d00c5f74255f56a5e366f4f77f5a186d7f55',
                        '0x0d8775f648430679a709e98d2b0cb6250d2887ef',
                        '0xf17e65822b568b3903685a7c9f496cf7656cc6c2',
                        '0x1a4b46696b2bb4794eb3d4c26f1c55f9170fa4c5',
                        '0xb8c77482e45f1f44de1745f52c74426c631bdd52',
                        '0xb8c77482e45f1f44de1745f52c74426c631bdd52',
                        '0x1f573d6fb3f13d689ff844b4ce37794d79a7ff1c',
                        '0xcb97e65f07da24d46bcdd078ebebd7c6e6e3d750',
                        '0x4fabb145d64652a948d72533023f6e7a623c7c53',
                        '0xaaaebe6fe48e54f431b0c390cfaf0b017d09d42d',
                        '0x4f9254c83eb525f9fcf346490bbb3ed28a81c667',
                        '0xc00e94cb662c3520282e6f5717214004a7f26888',
                        '0x2ba592f78db6436527729929aaf6c908497cb200',
                        '0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b',
                        '0xd533a949740bb3306d119cc777fa900ba034cd52',
                        '0x4e3fbd56cd56c3e72c1403e103b45db9da5b9d2b',
                        '0x6b175474e89094c44da98b954eedeac495271d0f',
                        '0x0abdace70d3790235af448c88547603b945604ea',
                        '0x43dfc4159d86f3a37a5a4b3d4580b888ad7d4ddd',
                        '0x1494ca1f11d487c2bbe4543e90080aeba4ba3c2b',
                        '0x92d6c1e31e14520e676a687f0a93788b716beff5', ]

    def test_1inch(self):
        self.run_model('price.one-inch', {"base": "0xdac17f958d2ee523a2206206994597c13d831ec7"})
        self.run_model('price.one-inch', {"base": "WETH"})
        self.run_model('price.one-inch', {"base": "USDC"})
        self.run_model('price.one-inch', {"base": "AAVE"})
        self.run_model('price.one-inch', {"base": "CMK"})
        self.run_model('price.one-inch', {"base": "ETH"})

    def test_currency_dto(self):
        self.title('Price - Currency DTO')
        for prefer in ['cex', 'dex']:
            self.run_model('price.quote', {"base": "CMK", "prefer": prefer})
            self.run_model('price.quote', {"base": "EUR", "prefer": prefer})
            self.run_model('price.quote', {"base": "EUR", "quote": "JPY", "prefer": prefer})
            self.run_model('price.quote', {"base": "ETH", "quote": "JPY", "prefer": prefer})
            self.run_model('price.quote', {"base": "AAVE", "quote": "ETH", "prefer": prefer})
            self.run_model('price.quote', {"base": "0x853d955acef822db058eb8505911ed77f175b99e", "prefer": prefer})

    def test_historical(self):
        self.title('Price - Historical')
        self.run_model('price.quote', {'base': 'AAVE'}, block_number=11266884)

    def test_price_general(self):
        self.title('Price - General')

        self.run_model('price.quote', {"base": "0x6c3f90f043a72fa612cbac8115ee7e52bde6e490"})
        self.run_model('price.quote', {"base": "0x075b1bb99792c9e1041ba13afef80c91a1e70fb3"})
        self.run_model('price.quote', {"base": "0xc4ad29ba4b3c580e6d59105fff484999997675ff"})

        self.run_model('price.dex-blended', {"symbol": "CMK"})  # price.pool-aggregator

        # aDAI v1: 0xfC1E690f61EFd961294b3e1Ce3313fBD8aa4f85d
        self.run_model('token.underlying-maybe', {"address": "0xfC1E690f61EFd961294b3e1Ce3313fBD8aa4f85d"})
        # aDAI V2: 0x028171bCA77440897B824Ca71D1c56caC55b68A3
        self.run_model('token.underlying-maybe', {"address": "0x028171bCA77440897B824Ca71D1c56caC55b68A3"})

        # aETHb 0xd01ef7c0a5d8c432fc2d1a85c66cf2327362e5c6
        self.run_model('price.quote', {"base": {"address": "0xd01ef7c0a5d8c432fc2d1a85c66cf2327362e5c6"}})

        # aETHc 0xE95A203B1a91a908F9B9CE46459d101078c2c3cb
        self.run_model('price.quote', {"base": {"address": "0xE95A203B1a91a908F9B9CE46459d101078c2c3cb"}})

        self.run_model('price.quote', {"base": {"address": "0xfC1E690f61EFd961294b3e1Ce3313fBD8aa4f85d"}})
        self.run_model('price.quote', {"base": {"address": "0x028171bCA77440897B824Ca71D1c56caC55b68A3"}})

        self.run_model('price.quote-historical', {"base": {"symbol": "AAVE"},
                       "interval": 86400, "count": 1, "exclusive": True})
        self.run_model('price.quote-multiple', {"some": [{"base": {"symbol": "EUR"}}, {"base": {"symbol": "JPY"}}]})
        self.run_model('price.quote-historical-multiple',
                       {"some": [{"base": {"symbol": "AAVE"}}], "interval": 86400, "count": 1, "exclusive": True})
        self.run_model('finance.var-dex-lp', {"pool": {"address": "0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58"},
                       "window": "10 days", "interval": 1, "confidence": 0.01, "lower_range": 0.01, "upper_range": 0.01})

    def test_dex_curve(self):
        self.title('Price - General')
        block_number = 15000108

        # 0xdB06a76733528761Eda47d356647297bC35a98BD
        self.title('Price - dex-Curve')

        token_addrs = ['0xFEEf77d3f69374f66429C91d732A244f074bdf74',
                       '0x6c3f90f043a72fa612cbac8115ee7e52bde6e490',
                       '0xADF15Ec41689fc5b6DcA0db7c53c9bFE7981E655',
                       '0x8e595470ed749b85c6f7669de83eae304c2ec68f',
                       '0x76eb2fe28b36b3ee97f3adae0c69606eedb2a37c',
                       '0x48759f220ed983db51fa7a8c0d2aab8f3ce4166a']

        for token_addr in token_addrs:
            if token_addr.startswith('0x'):
                token_input = {"address": token_addr}
            else:
                token_input = {"symbol": token_addr}

            self.run_model('price.dex-curve-fi-maybe', token_input,
                           block_number=block_number)  # __all__ # price.dex-curve-fi
            self.run_model('price.quote', {"base": token_input, "quote": {
                           "symbol": "USD"}}, block_number=block_number)  # __all__
            self.run_model('price.quote', {"quote": token_input, "base": {
                           "symbol": "USD"}}, block_number=block_number)  # __all__

    def test_price_dex(self):
        self.title('Price - Dex')
        block_number = 15981401

        self.run_model('price.dex', {"base": "CMK", "quote": "USD"}, block_number=block_number)
        self.run_model('price.dex', {"quote": "CMK", "base": "USD"}, block_number=block_number)
        self.run_model('price.dex', {"base": "CMK", "quote": "EUR"}, block_number=block_number)
        self.run_model('price.dex', {"quote": "CMK", "base": "EUR"}, block_number=block_number)
        self.run_model('price.dex', {"base": "CMK", "quote": "AAVE"}, block_number=block_number)
        self.run_model('price.dex', {"quote": "CMK", "base": "AAVE"}, block_number=block_number)

    def test_price_cex(self):
        self.title('Price - Cex')
        block_number = 15981401

        self.run_model('price.cex', {"base": "AAVE", "quote": "USD"}, block_number=block_number)
        self.run_model('price.cex', {"quote": "AAVE", "base": "USD"}, block_number=block_number)
        self.run_model('price.cex', {"base": "AAVE", "quote": "EUR"}, block_number=block_number)
        self.run_model('price.cex', {"quote": "AAVE", "base": "EUR"}, block_number=block_number)
        self.run_model('price.cex', {"base": "LINK", "quote": "AAVE"}, block_number=block_number)
        self.run_model('price.cex', {"quote": "LINK", "base": "AAVE"}, block_number=block_number)

    def test_dex_prefer(self) -> None:
        self.run_model('price.dex-db-prefer', {"symbol": "AAVE"})
        self.run_model('price.dex-db-prefer', {"symbol": "AAVE"}, block_number=15981401)

    def test_chainlink(self):
        self.title('Price - Chainlink Oracle')
        block_number = 15000108

        # 0x767FE9EDC9E0dF98E07454847909b5E959D7ca0E ilv
        # 0x383518188C0C6d7730D91b2c03a03C837814a899 ohm-eth.data.eth
        # 0x64aa3364F17a4D01c6f1751Fd97C2BD3D7e7f1D5 ohmv2-eth.data.eth
        # 0xc7283b66Eb1EB5FB86327f08e1B5816b0720212B tribe-eth.data.eth
        # 0xFEEf77d3f69374f66429C91d732A244f074bdf74 price-curve

        tokens = ['WBTC',
                  'BTC',
                  'USD',
                  'ETH',
                  'CNY',
                  'USDC',
                  'GBP',
                  '0x85f138bfEE4ef8e540890CFb48F620571d67Eda3',
                  '0xcb97e65f07da24d46bcdd078ebebd7c6e6e3d750',
                  '0xD31a59c85aE9D8edEFeC411D448f90841571b89c',
                  '0xB8c77482e45F1F44dE1745F52C74426C631bDD52',
                  '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                  '0xD31a59c85aE9D8edEFeC411D448f90841571b89c',
                  '0x767FE9EDC9E0dF98E07454847909b5E959D7ca0E',
                  '0x1a4b46696b2bb4794eb3d4c26f1c55f9170fa4c5',
                  '0x64aa3364F17a4D01c6f1751Fd97C2BD3D7e7f1D5',
                  '0xc7283b66Eb1EB5FB86327f08e1B5816b0720212B',
                  '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599',
                  '0x383518188C0C6d7730D91b2c03a03C837814a899']

        models = ['price.quote', 'price.oracle-chainlink']

        for price_model in models:
            for token_addr in tokens:
                for prefer in ['cex', 'dex']:
                    if token_addr.startswith('0x'):
                        token_input = {"address": token_addr}
                    else:
                        token_input = {"symbol": token_addr}

                    self.run_model(price_model, {"base": token_input, "quote": {
                        "symbol": "USD", "prefer": prefer}}, block_number=block_number)  # __all__
                    self.run_model(price_model, {"quote": token_input, "base": {
                        "symbol": "USD", "prefer": prefer}}, block_number=block_number)  # __all__
                    self.run_model(price_model, {"base": token_input, "quote": {
                        "symbol": "JPY", "prefer": prefer}}, block_number=block_number)  # __all__
                    self.run_model(price_model, {"quote": token_input, "base": {
                        "symbol": "JPY", "prefer": prefer}}, block_number=block_number)  # __all__
                    self.run_model(price_model, {"base": token_input, "quote": {
                        "symbol": "GBP", "prefer": prefer}}, block_number=block_number)  # __all__
                    self.run_model(price_model, {"quote": token_input, "base": {
                        "symbol": "GBP", "prefer": prefer}}, block_number=block_number)  # __all__
                    self.run_model(price_model, {"base": token_input, "quote": {
                        "symbol": "EUR", "prefer": prefer}}, block_number=block_number)  # __all__
                    self.run_model(price_model, {"quote": token_input, "base": {
                        "symbol": "EUR", "prefer": prefer}}, block_number=block_number)  # __all__
                    self.run_model(price_model, {"base": token_input, "quote": {
                        "address": "0xD31a59c85aE9D8edEFeC411D448f90841571b89c"},
                        "prefer": prefer}, block_number=block_number)  # __all__
                    self.run_model(price_model, {"quote": token_input, "base": {
                        "address": "0xD31a59c85aE9D8edEFeC411D448f90841571b89c"},
                        "prefer": prefer}, block_number=block_number)  # __all__


def run_test_price_mix(self, tok):
    block_number = 15000108
    for prefer in ['cex', 'dex']:
        if prefer == 'dex' and tok not in TestPrice.CEX_ONLY_TOKENS:
            self.run_model('price.quote',
                           {"base": {"address": tok}, "quote": {"symbol": "USD"}, "prefer": prefer},
                           block_number=block_number)
            self.run_model('price.quote',
                        {"base": {"address": tok}, "quote": {"symbol": "EUR"}, "prefer": prefer},
                        block_number=block_number)

        if prefer == 'cex':
            self.run_model('price.quote',
                           {"quote": {"address": tok}, "base": {"symbol": "USD"}, "prefer": prefer},
                           block_number=block_number)
            self.run_model('price.quote',
                           {"quote": {"address": tok}, "base": {"symbol": "EUR"}, "prefer": prefer},
                           block_number=block_number)

    self.run_model('price.oracle-chainlink', {"base": {"address": tok},
                                              "quote": {"symbol": "USD"}}, block_number=block_number)
    self.run_model('price.oracle-chainlink', {"quote": {"address": tok},
                                              "base": {"symbol": "USD"}}, block_number=block_number)

    self.run_model('price.oracle-chainlink', {"base": {"address": tok},
                                              "quote": {"symbol": "EUR"}}, block_number=block_number)
    self.run_model('price.oracle-chainlink', {"quote": {"address": tok},
                                              "base": {"symbol": "EUR"}}, block_number=block_number)

    self.run_model('price.oracle-chainlink', {"base": {"address": tok},
                                              "quote": {"symbol": "AAVE"}}, block_number=block_number)
    self.run_model('price.oracle-chainlink', {"quote": {"address": tok},
                                              "base": {"symbol": "AAVE"}}, block_number=block_number)


for n, token in enumerate(TestPrice.CHAINLINK_TOKENS):
    setattr(TestPrice, f'test_price_mix_{n+1}',
            lambda self, token=token: run_test_price_mix(self, tok=token))
