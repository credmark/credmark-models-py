# pylint:disable=locally-disabled,line-too-long,unused-import

from datetime import datetime, timezone

from cmf_test import CMFTest
from credmark.cmf.types import Network

from models.credmark.protocols.lending.compound.compound_v3 import CompoundV3Meta


class TestCompound(CMFTest):
    def test_deployment(self):
        self.title('Compound')

        self.run_model('compound-v2.get-comptroller')
        self.run_model('compound-v2.get-pools')

    def test_pool(self):
        tokens = {
            'cMKR': '0x95b4ef2869ebd94beb4eee400a99824bf5dc325b',
            'cCOMP': '0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4',
            'cUSDC': '0x39aa39c021dfbae8fac545936693ac917d5e7563',
            'cDAI': '0x5d3a536e4d6dbd6114cc1ead35777bab948e3643',
        }

        for _symbol, address in tokens.items():
            self.run_model('compound-v2.pool-info',
                           {"address": address})

    def test_portfolio(self):
        self.run_model('compound-v2.all-pools-info', {}, block_number=12770589)
        self.run_model('compound-v2.all-pools-portfolio', {}, block_number=12770589)

        self.run_model('compound-v2.all-pools-info')
        self.run_model('compound-v2.all-pools-value')
        self.run_model('compound-v2.all-pools-portfolio')

    def test_historical(self):
        dates = [
            datetime(2021, 9, 20, tzinfo=timezone.utc),
            datetime(2021, 12, 18, tzinfo=timezone.utc),
            datetime(2022, 1, 18, tzinfo=timezone.utc),
        ]

        for dt in dates:
            block_number = self.run_model_with_output(
                'chain.get-block',
                {'timestamp': int(dt.timestamp())})['output']['block_number']

            self.run_model('historical.run-model',
                           {'model_slug': 'compound-v2.pool-value',
                            'window': '5 days',
                            'interval': '1 days',
                            'model_input': {'address': '0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4'}},
                           block_number=block_number)

    def test_account(self):
        self.run_model('compound-v2.account',
                       {"address": "0xFCcE99EC4f62F0a6714dABda4571968005cA8C64"},
                       block_number=17768798)


class TestCompoundV3(CMFTest):
    def test_markets(self):
        """
        credmark-dev run compound-v3.market -j -c 1
        credmark-dev run compound-v3.market -j -c 137
        credmark-dev run compound-v3.market -j -c 42161
        """
        self.title('Compound V3')

        for network in CompoundV3Meta.MARKETS:
            # if network == Network.Mainnet:
            self.run_model('compound-v3.market', {}, chain_id=network.value, latest_block=True)

    def test_account(self):
        """
        # Withdraw @ 17814775 / Borrow in WETH
        # Tx: 0x80cd56d104782d1c1aea4d9766bf52f4c9d33859b0bb834a0272ec196eee116a
        credmark-dev run compound-v3.account -i '{"address": "0xB9ACd5304E42eE02288bb06ccE4403449f23D5fc"}' -b 17814774 -j

        # WithdrawCollateral @ 17817319 WETH
        # via 0xa397a8C2086C554B531c02E29f3291c9704B00c7 (Compound Deployer), find the other transfer out account
        # Tx: 0x38da948b42f00a5bff02a406debf91699dc15767cae816deb662a9a6c799a1b3
        credmark-dev run compound-v3.account -i '{"address": "0x52efFC15dFAA1eFC701a8b9522654E4e1C99b012"}' -b 17817318 -j

        # Supply @ 45761507
        # Tx: 0xa10a84c73d45b885e31c2f7968fccb73d1f6128dfa02a335daf40047aa0926c3
        credmark-dev run compound-v3.account -i '{"address": "0x7d211b6312cb7a614276bc7eb511973cb4e985be"}' -c 137 -b 45761507 -j

        # SupplyCollateral @ 45759515
        # Tx: 0x1597f2cb61e06a9ea2f96924d13bcc3d1511ced3e47ac2a456277ca6724d6718
        credmark-dev run compound-v3.account -i '{"address": "0x59e242d352ae13166b4987ae5c990c232f7f7cd6"}' -c 137 -b 45759515 -j

        # WithdrawCollateral @ 45762294
        # Tx: 0x33e2db31a75dd8a54cced6e9c0dd3bdaab18fc4d95b687a70ff70c57f713925f
        credmark-dev run compound-v3.account -i '{"address": "0x4e56e288A7743f7af3771a3eCB0F86D1976bb8f3"}' -c 137 -b 45762293 -j

        # Supply @ 116926424
        # SupplyCollateral @ 116926261
        credmark-dev run compound-v3.account -i '{"address": "0x109b3c39d675a2ff16354e116d080b94d238a7c9"}' -c 42161 -b 116926424 -j
        """

        self.run_model('compound-v3.account',
                       {"address": "0xB9ACd5304E42eE02288bb06ccE4403449f23D5fc"}, block_number=17814774)
        self.run_model('compound-v3.account',
                       {"address": "0x52efFC15dFAA1eFC701a8b9522654E4e1C99b012"}, block_number=17817318)

        self.run_model('compound-v3.account',
                       {"address": "0x7d211b6312cb7a614276bc7eb511973cb4e985be"}, chain_id=137, block_number=45761507)
        self.run_model('compound-v3.account',
                       {"address": "0x59e242d352ae13166b4987ae5c990c232f7f7cd6"}, chain_id=137, block_number=45759515)

        self.run_model('compound-v3.account',
                       {"address": "0x4e56e288A7743f7af3771a3eCB0F86D1976bb8f3"}, chain_id=42161, block_number=116926424)
