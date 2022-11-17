# pylint:disable=locally-disabled,line-too-long

from cmk_test import CMKTest


class TestAccount(CMKTest):
    def test_account(self):
        # account.token-erc20
        self.run_model('account.token-erc20', {"address": "0x109B3C39d675A2FF16354E116d080B94d238a7c9"})
        self.run_model('account.token-erc20', {"address": "0x195e8cd1cca12fd18643000c6d4e21b766d92a10"})

        self.run_model('account.token-erc20', {'address': '0x9c5083dd4838e120dbeac44c052179692aa5dac5'})

        self.run_model('account.position-in-curve', {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"})
        self.run_model('account.portfolio', {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"})

        self.run_model('account.portfolio-aggregate',
                       {"accounts": [{"address": "0x109B3C39d675A2FF16354E116d080B94d238a7c9"}]})

        self.run_model('account.portfolio-aggregate', {"accounts": [{"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"}, {
                       "address": "0xAE5B61a270e77F41b99965B171e20DFA8642E0Ea"}]})

        self.run_model('account.var', {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636",
                       "window": "3 days", "interval": 1, "confidence": 0.01})

        self.run_model('account.var', {"address": "0x912a0a41b820e1fa660fb6ec07fff493e015f3b2",
                       "window": "3 days", "interval": 1, "confidence": 0.01})

        self.run_model('account.portfolio', {"address": "0x8180D59b7175d4064bDFA8138A58e9baBFFdA44a"})
        self.run_model('account.portfolio', {"address": "0x049355e4380f8DB88Cb8a6ec0426B1a1A3560c67"})

        self.run_model('token.logo', {"symbol": "AAVE"})
        self.run_model('token.balance', {"symbol": "AAVE",
                                         "account": "0xAeCf596D2286940b8DA0AB14b07619F01E8213f2"})
        self.run_model('token.balance', {"address": "0x0ab87046fBb341D058F17CBC4c1133F25a20a52f",
                                         "account": "0xAeCf596D2286940b8DA0AB14b07619F01E8213f2"})

        # 1. address for the ren community funds
        # 0x5291fBB0ee9F51225f0928Ff6a83108c86327636
        self.run_model('account.token-return',
                       {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636", "token_list": "cmf"})
        self.run_model('account.token-return',
                       {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636", "token_list": "all"})

        self.run_model('account.token-return', {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636", "token_list": "all"},
                       block_number=15447136)

        # Long-loading account
        # self.run_model('account.token-return', {"address": "0x195e8cd1cca12fd18643000c6d4e21b766d92a10"})

        # 2. UMA treasury
        # 0x8180D59b7175d4064bDFA8138A58e9baBFFdA44a
        # 0x049355e4380f8DB88Cb8a6ec0426B1a1A3560c67
        self.run_model('account.token-return',
                       {"address": "0x8180D59b7175d4064bDFA8138A58e9baBFFdA44a", "token_list": "cmf"}, block_number=15447136)
        self.run_model('account.token-return',
                       {"address": "0x049355e4380f8DB88Cb8a6ec0426B1a1A3560c67", "token_list": "cmf"}, block_number=15447136)

        self.run_model('accounts.token-return',
                       {"accounts": ["0x8180D59b7175d4064bDFA8138A58e9baBFFdA44a",
                                     "0x049355e4380f8DB88Cb8a6ec0426B1a1A3560c67"],
                        "token_list": "cmf"},
                       block_number=15447136)

        # empty address
        self.run_model('accounts.token-return', {"accounts": [], "token_list": "cmf"})

        # invalid address
        self.run_model('accounts.token-return',
                       {"accounts": ["0x109B3C39d675A2FF16354E116d080B94d238a7c8"],
                        "token_list": "cmf"
                        })

        # a few address
        self.run_model('accounts.token-return',
                       {"accounts": ["0x109B3C39d675A2FF16354E116d080B94d238a7c9", "0x109B3C39d675A2FF16354E116d080B94d238a7c9"],
                        "token_list": "cmf"})

        self.run_model('account.token-return',
                       {"address": "0x109B3C39d675A2FF16354E116d080B94d238a7c8", "token_list": "cmf"})
        self.run_model('account.token-return',
                       {"address": "0x109B3C39d675A2FF16354E116d080B94d238a7c9", "token_list": "cmf"})

        # token-historical, token-return-historical
        self.run_model('account.token-historical',
                       {"accounts": "0x109B3C39d675A2FF16354E116d080B94d238a7c9",
                        "token_list": "cmf", "window": "5 days", "interval": "1 days"})

        self.run_model('account.token-return-historical',
                       {"accounts": "0x109B3C39d675A2FF16354E116d080B94d238a7c9",
                        "token_list": "cmf", "window": "5 days", "interval": "1 days"})
