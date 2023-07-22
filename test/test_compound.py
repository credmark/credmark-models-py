# pylint:disable=locally-disabled,line-too-long

from datetime import datetime, timezone

from cmf_test import CMFTest


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

        for address in tokens:
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
