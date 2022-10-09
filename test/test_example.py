# pylint:disable=locally-disabled,line-too-long

from cmk_test import CMKTest


class TestExample(CMKTest):
    def test(self):
        self.title('Neil\'s example')
        self.run_model('contrib.neilz', {})

        self.run_model('contrib.neilz-new-addresses', {"start_block": -100, "unique": True})
        self.run_model('contrib.neilz-new-addresses', {"start_block": 15709159}, block_number=15709259)

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
