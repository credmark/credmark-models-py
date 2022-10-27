# pylint:disable=locally-disabled,line-too-long

from cmk_test import CMKTest


class TestExample(CMKTest):
    def test(self):
        self.title('Neil\'s example')
        self.run_model('contrib.neilz', {})

        self.run_model('contrib.neilz-new-addresses', {"start_block": -100, "unique": True})
        self.run_model('contrib.neilz-new-addresses', {"start_block": 15709159}, block_number=15709259)

        self.run_model('contrib.curve-fi-pool-historical-reserve',
                       {"address": "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46"})

        self.title('Example')
        self.run_model('example.all', {})  # example.contract, example.ledger-transactions, example.block-time
        self.run_model('example.model', {})
        self.run_model('example.model-run', {})
        self.run_model('example.contract', {})

        self.run_model('example.data-error-1', {}, exit_code=3)
        self.run_model('example.data-error-2', {}, exit_code=3)

        self.run_model('example.block-time', {})
        self.run_model('example.block-number', {})
        self.run_model('example.address', {})
        self.run_model('example.libraries', {})
        self.run_model('example.token', {})
        self.run_model('example.dto', {})
        self.run_model('example.dto-type-test-1',
                       {"positions": [{"amount": "4.2", "asset": {"symbol": "USDC"}}, {"amount": "4.4", "asset": {"symbol": "USDT"}}]})
        self.run_model('example.dto-type-test-2', {"positions": [{"amount": "4.2", "asset": {"symbol": "USDC"}}, {
                       "amount": "4.4", "asset": {"symbol": "USDT"}}]}, exit_code=1)
        self.run_model('example.account', {})
        self.run_model('example.ledger-aggregates', {})

        self.title('Historical Examples')
        self.run_model('example.historical', {"model_slug": "price.quote",
                       "model_input": {"base": {"symbol": "USDC"}}})  # price.quote
        # token.overall-volume  # series.time-window-interval, series.time-start-end-interval
        self.run_model('example.historical', {"model_slug": "token.overall-volume", "model_input": {"symbol": "USDC"}})
        # example.libraries  # series.block-window-interval, series.block-start-end-interval
        self.run_model('example.historical-block', {})

        self.title('Ledger Examples')
        self.run_model('example.ledger-token-transfers', {"address": "0x3812D217bB3A0B43aa16985A616A4e0c6A17C65F"})
        self.run_model('example.ledger-transactions', {})
        self.run_model('example.ledger-receipts', {})
        self.run_model('example.ledger-traces', {})
        self.run_model('example.ledger-blocks', {})
        self.run_model('example.ledger-tokens', {})
        self.run_model('example.ledger-contracts', {})
        self.run_model('example.ledger-logs', {})

        self.title('Iteration Examples')
        self.run_model('example.iteration', {})

        self.run_model('contrib.token-net-inflow', {'blocks': 7000}, block_number=15038786)
        self.run_model('contrib.debt-dao-generalized-cashflow',
                       {"sender_address": "0xf16E9B0D03470827A95CDfd0Cb8a8A3b46969B91",
                           "receiver_address": "0xf596c85d4ec5572dfB2351F9395ca6A185aAec6D"},
                       block_number=15086281)
        self.run_model('contrib.neilz-redacted-votium-cashflow', {}, block_number=15086281)
        self.run_model('contrib.neilz-redacted-convex-cashflow', {}, block_number=15086281)

        self.run_model('contrib.uniswap-fee', {"interval": 500}, block_number=15211790)

    def test_convex_apr(self):
        test_cases = [{
            'lp_token': '0x43b4fdfd4ff969587185cdb6f0bd875c5fc83f8c',
            'reward': '0x02e2151d4f351881017abdf2dd2b51150841d5b3'
        },
            {
            'lp_token': '0xd2967f45c4f384deea880f807be904762a3dea07',
            'reward': '0x7a7bbf95c44b144979360c3300b54a7d34b44985'
        },
            {
            'lp_token': '0x5b5cfe992adac0c9d48e05854b2d91c73a003858',
            'reward': '0x353e489311b21355461353fec2d02b73ef0ede7f'
        },
            {
            'lp_token': '0x4f3e8f405cf5afc05d68142f3783bdfe13811522',
            'reward': '0x4a2631d090e8b40bbde245e687bf09e5e534a239'
        },
            {
            'lp_token': '0x1aef73d49dedc4b1778d0706583995958dc862e6',
            'reward': '0xdbfa6187c79f4fe4cda20609e75760c5aae88e52'
        },
            {
            'lp_token': '0xfd2a8fa60abd58efe3eee34dd494cd491dc14900',
            'reward': '0xe82c1eb4bc6f92f85bf7eb6421ab3b882c3f5a7b'
        },
            {
            'lp_token': '0x7eb40e450b9655f4b3cc4259bcc731c63ff55ae6',
            'reward': '0x24dffd1949f888f91a0c8341fc98a3f280a782a8'
        },
            {
            'lp_token': '0xd632f22692fac7611d2aa1c0d552930d43caed3b',
            'reward': '0xb900ef131301b307db5efcbed9dbb50a3e209b2e'
        },
            {
            'lp_token': '0xEd279fDD11cA84bEef15AF5D39BB4d4bEE23F0cA',
            'reward': '0x2ad92a7ae036a038ff02b96c88de868ddf3f8190'
        }]

        for tc in test_cases[:3]:
            self.run_model('contrib.curve-convex-yield', tc, block_number=15839025)
