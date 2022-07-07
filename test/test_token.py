# pylint:disable=locally-disabled,line-too-long

from cmk_test import CMKTest


class TestToken(CMKTest):
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

        self.run_model('token.holders', {"symbol": "CMK"})
        self.run_model('token.swap-pools', {"symbol": "CMK"})
        self.run_model('token.info', {"symbol": "CMK"})
        self.run_model('token.info', {"address": "0x019Ff0619e1D8Cd2d550940eC743fDE6d268AfE2"})
        self.run_model('token.info', {"address": "0x019ff0619e1d8cd2d550940ec743fde6d268afe2"})

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
        self.run_model('account.position-in-curve', {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"})
        self.run_model('account.portfolio', {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"})
        self.run_model('account.portfolio-aggregate', {"accounts": [{"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"}, {
                       "address": "0xAE5B61a270e77F41b99965B171e20DFA8642E0Ea"}]})

        self.run_model('account.var', {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636",
                       "window": "3 days", "interval": 1, "confidence": 0.01})
