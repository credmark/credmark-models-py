# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestFiat(CMFTest):
    def test_volume(self):
        self.run_model('price.dex-db',
                       {'address': 'JPY'}, block_number=15945743)

        self.run_model('price.dex-db',
                       {'address': '0x0000000000000000000000000000000000000024'}, block_number=15945743)

        self.run_model('price.dex-db-series',
                       {'address': 'JPY', "start": 15945733, "end": 15945743, "interval": 2}, block_number=15945743)

        self.run_model('price.dex-db-series',
                       {'address': '0x0000000000000000000000000000000000000024', "start": 15945733, "end": 15945743, "interval": 2}, block_number=15945743)

        self.run_model('price.dex-db-interval',
                       {'address': 'JPY', "start": 1670856455, "end": 1671461255, "interval": 3600}, block_number=16365111)

        self.run_model('price.dex-db-interval',
                       {'address': '0x0000000000000000000000000000000000000024', "start": 1670856455, "end": 1671461255, "interval": 3600}, block_number=16365111)

        self.run_model('price.dex-db-latest',
                       {'address': '0x0000000000000000000000000000000000000188'})

        self.run_model('price.dex-db-latest',
                       {'address': 'JPY'})
