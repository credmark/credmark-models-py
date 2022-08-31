# pylint:disable=locally-disabled,line-too-long

from numpy import block
from cmk_test import CMKTest


class TestToken(CMKTest):
    def test_volume(self):
        self.run_model('token.overall-volume-block',
                       {'symbol': 'USDC', 'block_number': -1000})

        self.run_model('token.overall-volume-block',
                       {'symbol': 'USDC', 'block_number': self.block_number - 1000})

        self.run_model('token.overall-volume-window',
                       {'symbol': 'USDC', 'window': '24 hours'})

    def test_holders(self):
        self.run_model(
            'token.holders',
            {"address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "top_n": 20})

        self.run_model(
            'token.holders',
            {"address": "0xFFC97d72E13E01096502Cb8Eb52dEe56f74DAD7B", "top_n": 20})

    def test_transaction(self):
        self.run_model(
            'token.transaction',
            {"hash": "0x319552805d5f3d0c97e7b6c1e40d0c42817c49406fbff41af0f3ac88b590aa34", "block_number": 15125867}, block_number=15225867)

        self.run_model(
            'token.transaction',
            {"hash": "0x7ee67c4b2b5540a503fdf3b2f3a44c955c22884c0e286f5d89e67d4d8989264a", "block_number": 13984858}, block_number=15125867)

    def test_account(self):
        self.title("Account Examples")
        self.run_model('account.portfolio', {"address": "0xCE017A1dcE5A15668C4299263019c017154ACE17"})

        # Working but taking long time.
        # Test account 1: 0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0
        # Test account 2: 0xbdfa4f4492dd7b7cf211209c4791af8d52bf5c50
        # self.run_model('account.portfolio', {"address": "0xbdfa4f4492dd7b7cf211209c4791af8d52bf5c50"})

    def test_tokens(self):
        self.title("Token Examples")

        # UniswapV3 pool USDC-WETH 0x7bea39867e4169dbe237d55c8242a8f2fcdcc387
        self.run_model('uniswap-v3.get-pool-info', {"address": "0x7bea39867e4169dbe237d55c8242a8f2fcdcc387"})

        # token.underlying-maybe,price.oracle-chainlink-maybe,price.oracle-chainlink
        self.run_model('price.quote', {"base": {"symbol": "WETH"}})  # ${token_price_deps}
        self.run_model('price.quote', {"base": {"symbol": "CMK"}})  # ${token_price_deps}
        self.run_model('price.quote', {"base": {"symbol": "AAVE"}})  # ${token_price_deps}

        # AAVE: 0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9
        # ${token_price_deps}
        self.run_model('price.quote', {"base": {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9"}})
        self.run_model('price.quote', {"base": {"symbol": "USDC"}})  # ${token_price_deps}
        self.run_model('price.quote', {"base": {"symbol": "MKR"}})  # ${token_price_deps}

        # Ampleforth: 0xd46ba6d942050d489dbd938a2c909a5d5039a161
        # ${token_price_deps}
        self.run_model('price.quote', {"base": {"address": "0xd46ba6d942050d489dbd938a2c909a5d5039a161"}})
        # RenFil token: 0xD5147bc8e386d91Cc5DBE72099DAC6C9b99276F5
        # ${token_price_deps}
        self.run_model('price.quote', {"base": {"address": "0xD5147bc8e386d91Cc5DBE72099DAC6C9b99276F5"}})

        self.run_model('token.holders', {"symbol": "CMK"})
        self.run_model('token.swap-pools', {"symbol": "CMK"})
        self.run_model('token.info', {"symbol": "CMK"})
        self.run_model('token.info', {"address": "0x019Ff0619e1D8Cd2d550940eC743fDE6d268AfE2"})
        self.run_model('token.info', {"address": "0x019ff0619e1d8cd2d550940ec743fde6d268afe2"})

        # WETH-DAI pool: https://analytics.sushi.com/pairs/0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f
        self.run_model('token.swap-pool-volume', {"address": "0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f"})

        # UniSwap V3 factory: 0x1F98431c8aD98523631AE4a59f267346ea31F984
        self.run_model('token.categorized-supply', {"categories": [{"accounts": {"accounts": [
                       {"address": "0x1F98431c8aD98523631AE4a59f267346ea31F984"}]}, "categoryName": "", "categoryType": "", "circulating": True}], "token": {"symbol": "DAI"}})

        # account.token-erc20
        self.run_model('account.token-erc20', {"address": "0x109B3C39d675A2FF16354E116d080B94d238a7c9"})
        self.run_model('account.position-in-curve', {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"})
        self.run_model('account.portfolio', {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"})
        self.run_model('account.portfolio-aggregate', {"accounts": [{"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"}, {
                       "address": "0xAE5B61a270e77F41b99965B171e20DFA8642E0Ea"}]})

        self.run_model('account.var', {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636",
                       "window": "3 days", "interval": 1, "confidence": 0.01})

        self.run_model('account.var', {"address": "0x912a0a41b820e1fa660fb6ec07fff493e015f3b2",
                       "window": "3 days", "interval": 1, "confidence": 0.01})

        self.run_model('account.portfolio', {"address": "0x8180D59b7175d4064bDFA8138A58e9baBFFdA44a"})
        self.run_model('account.portfolio', {"address": "0x049355e4380f8DB88Cb8a6ec0426B1a1A3560c67"})

        # 1. address for the ren community funds
        # 0x5291fBB0ee9F51225f0928Ff6a83108c86327636
        self.run_model('account.token-return', {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"})

        self.run_model('account.token-return',
                       {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"}, block_number=15447136)

        # 2. UMA treasury
        # 0x8180D59b7175d4064bDFA8138A58e9baBFFdA44a
        # 0x049355e4380f8DB88Cb8a6ec0426B1a1A3560c67
        self.run_model('account.token-return',
                       {"address": "0x8180D59b7175d4064bDFA8138A58e9baBFFdA44a"}, block_number=15447136)
        self.run_model('account.token-return',
                       {"address": "0x049355e4380f8DB88Cb8a6ec0426B1a1A3560c67"}, block_number=15447136)

        self.run_model('accounts.token-return',
                       {"accounts": ["0x8180D59b7175d4064bDFA8138A58e9baBFFdA44a",
                                     "0x049355e4380f8DB88Cb8a6ec0426B1a1A3560c67"]},
                       block_number=15447136)
