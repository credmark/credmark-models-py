# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestAccount(CMFTest):
    def test_account_var(self):
        self.run_model('account.var', {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636",
                       "window": "3 days", "interval": 1, "confidence": 0.01})

        self.run_model('account.var', {"address": "0x912a0a41b820e1fa660fb6ec07fff493e015f3b2",
                       "window": "3 days", "interval": 1, "confidence": 0.01})

        self.run_model('account.portfolio', {
                       "address": "0x8180D59b7175d4064bDFA8138A58e9baBFFdA44a"})
        self.run_model('account.portfolio', {
                       "address": "0x049355e4380f8DB88Cb8a6ec0426B1a1A3560c67"})

    def test_token(self):
        self.run_model('token.logo', {"symbol": "AAVE"})
        self.run_model('token.balance', {"symbol": "AAVE",
                                         "account": "0xAeCf596D2286940b8DA0AB14b07619F01E8213f2"})
        self.run_model('token.balance', {"address": "0x0ab87046fBb341D058F17CBC4c1133F25a20a52f",
                                         "account": "0xAeCf596D2286940b8DA0AB14b07619F01E8213f2"})

    def test_account_token(self):
        # account.token-transfer
        self.run_model('account.token-transfer',
                       {"address": "0x109B3C39d675A2FF16354E116d080B94d238a7c9"})
        self.run_model('account.token-transfer',
                       {"address": "0x195e8cd1cca12fd18643000c6d4e21b766d92a10"})
        self.run_model('account.token-transfer',
                       {'address': '0x9c5083dd4838e120dbeac44c052179692aa5dac5'})

        # Console Test to return int
        # run_model('account.token-transfer', {"address":"0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"}, return_type=Records).to_dataframe().value.sum()
        # run_model('ledger.account-token-transfers', {"accounts": ["0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"], "blockNumber": self.context.block_number})

        # get_token_transfer(context, ['0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'], [], 0).value.sum()
        # get_native_transfer(context, ['0x109B3C39d675A2FF16354E116d080B94d238a7c9'])
        # get_native_transfer(context, ['0x109B3C39d675A2FF16354E116d080B94d238a7c9'], fix_int = False).value.sum

        self.run_model('accounts.token-transfer',
                       {"accounts": ["0x9c5083dd4838e120dbeac44c052179692aa5dac5", "0x109B3C39d675A2FF16354E116d080B94d238a7c9"]})

        self.run_model('accounts.token-transfer',
                       {"accounts": ["0x9c5083dd4838e120dbeac44c052179692aa5dac5", "0x109B3C39d675A2FF16354E116d080B94d238a7c9"],
                        "limit": 10})

        # Keep this out to avoid hitting size limit: "0x195e8cd1cca12fd18643000c6d4e21b766d92a10"
        self.run_model('accounts.token-transfer',
                       {"accounts": ["0x9c5083dd4838e120dbeac44c052179692aa5dac5",
                                     "0x109B3C39d675A2FF16354E116d080B94d238a7c9",
                                     ]})

    def test_account_portfolio(self):
        self.run_model(
            'curve.lp', {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"})
        self.run_model('curve.lp-accounts',
                       {"accounts": ["0x5291fBB0ee9F51225f0928Ff6a83108c86327636"]})

        self.run_model('account.portfolio', {
                       "address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"})

        self.run_model('accounts.portfolio',
                       {"accounts": [{"address": "0x109B3C39d675A2FF16354E116d080B94d238a7c9"}]})

        self.run_model('accounts.portfolio',
                       {"accounts": [{"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"},
                                     {"address": "0xAE5B61a270e77F41b99965B171e20DFA8642E0Ea"}]})

        self.run_model('account.portfolio', {
                       "address": "0x109B3C39d675A2FF16354E116d080B94d238a7c9"})
        self.run_model('accounts.portfolio',
                       {"accounts": ["0x109B3C39d675A2FF16354E116d080B94d238a7c9", "0x5291fBB0ee9F51225f0928Ff6a83108c86327636"]})

    def test_account_return(self):
        # 1. address for the ren community funds
        # 0x5291fBB0ee9F51225f0928Ff6a83108c86327636
        self.run_model('account.token-return',
                       {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636", "token_list": "cmf"})
        self.run_model('account.token-return',
                       {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636", "token_list": "all"})

        self.run_model('account.token-return',
                       {"address": "0x5291fBB0ee9F51225f0928Ff6a83108c86327636",
                           "token_list": "all"},
                       block_number=15447136)

        self.run_model('accounts.token-return',
                       {"accounts": ["0x5291fBB0ee9F51225f0928Ff6a83108c86327636"], "token_list": "cmf"})

        # 0x9c5083dd4838e120dbeac44c052179692aa5dac5 too long
        self.run_model('accounts.token-return',
                       {"accounts": ["0x5291fBB0ee9F51225f0928Ff6a83108c86327636",
                                     "0x109B3C39d675A2FF16354E116d080B94d238a7c9"], "token_list": "cmf"})

        self.run_model('accounts.token-return',
                       {"accounts": ["0x5291fBB0ee9F51225f0928Ff6a83108c86327636",
                                     "0x109B3C39d675A2FF16354E116d080B94d238a7c9"], "token_list": "all"})

        # Long-loading account
        # self.run_model('account.token-return', {"address": "0x195e8cd1cca12fd18643000c6d4e21b766d92a10"})

        # 2. UMA treasury
        # 0x8180D59b7175d4064bDFA8138A58e9baBFFdA44a relative small
        # 0x049355e4380f8DB88Cb8a6ec0426B1a1A3560c67
        self.run_model('account.token-return',
                       {"address": "0x8180D59b7175d4064bDFA8138A58e9baBFFdA44a", "token_list": "cmf"}, block_number=15447136)

        if '--api_url=http://localhost:8700' in self.post_flag:
            self.run_model('account.token-return',
                           {"address": "0x049355e4380f8DB88Cb8a6ec0426B1a1A3560c67", "token_list": "cmf"}, block_number=15447136)

        self.run_model('accounts.token-return',
                       {"accounts": ["0x8180D59b7175d4064bDFA8138A58e9baBFFdA44a",
                                     "0x049355e4380f8DB88Cb8a6ec0426B1a1A3560c67"],
                        "token_list": "cmf"},
                       block_number=15447136)

        # empty address
        self.run_model('accounts.token-return',
                       {"accounts": [], "token_list": "cmf"})

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

    def test_native_token_balance(self):
        # 1: mainnet
        # 137: polygon
        # 10: optimism
        # 56: bsc

        for chain_id in [1, 137, 10, 56]:
            latest_block_number = self.run_model_with_output(
                'chain.get-latest-block', {}, chain_id=chain_id)['output']['blockNumber'] - 100

            self.run_model('account.native-balance',
                           {"address": "0x42Cf18596EE08E877d532Df1b7cF763059A7EA57"},
                           chain_id=chain_id, block_number=latest_block_number)
            self.run_model('accounts.native-balance',
                           {"accounts": ["0x42Cf18596EE08E877d532Df1b7cF763059A7EA57"]},
                           chain_id=chain_id, block_number=latest_block_number)

    def test_token_historical(self):
        # token-historical, token-return-historical
        for acc_input in [{"address": "0x109B3C39d675A2FF16354E116d080B94d238a7c9"}]:
            self.run_model('account.token-historical',
                           acc_input | {"window": "5 days", "interval": "1 days"})
            self.run_model('account.token-return-historical',
                           acc_input | {"window": "5 days", "interval": "1 days"})

        # 0x9c5083dd4838e120dbeac44c052179692aa5dac5 contains NFT
        for accounts_input in [
            {"accounts": ["0x109B3C39d675A2FF16354E116d080B94d238a7c9"]},
            {"accounts": ["0x109B3C39d675A2FF16354E116d080B94d238a7c9",
                          "0x388C818CA8B9251b393131C08a736A67ccB19297"]},
            {"accounts": ["0x195e8cd1cca12fd18643000c6d4e21b766d92a10"]},
            {"accounts": ["0x195e8cd1cca12fd18643000c6d4e21b766d92a10",
                          "0x9c5083dd4838e120dbeac44c052179692aa5dac5"]},
            {"accounts": ["0x195e8cd1cca12fd18643000c6d4e21b766d92a10",
                          "0x9c5083dd4838e120dbeac44c052179692aa5dac5",
                          "0x109B3C39d675A2FF16354E116d080B94d238a7c9"]},
        ]:
            self.run_model('accounts.token-historical',
                           accounts_input | {"window": "5 days", "interval": "1 days"})
            self.run_model('accounts.token-historical',
                           accounts_input | {"window": "5 days", "interval": "1 days", 'quote': 'AAVE'})
            self.run_model('accounts.token-return-historical',
                           accounts_input | {"token_list": "cmf", "window": "5 days", "interval": "1 days"})
            self.run_model('accounts.token-historical',
                           accounts_input | {"window": "5 days", "interval": "1 days", "quote": "EUR"})

        # no price
        self.run_model('account.token-historical',
                       {"address": "0x5D7F34372FA8708E09689D400A613EeE67F75543", "window": "5 days", "interval": "1 day", "include_price": "false"})

    def test_token_leger(self):
        self.run_model('ledger.account-token-transfers',
                       {"accounts": ["0x109B3C39d675A2FF16354E116d080B94d238a7c9",
                                     "0x388C818CA8B9251b393131C08a736A67ccB19297"]},
                       block_number=16017203)

        self.run_model('ledger.account-native-token-transfers',
                       {"accounts": ["0x109B3C39d675A2FF16354E116d080B94d238a7c9",
                                     "0x388C818CA8B9251b393131C08a736A67ccB19297"]},
                       block_number=16017203)
