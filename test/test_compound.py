# pylint:disable=locally-disabled,line-too-long

from cmk_test import CMKTest


class TestCompound(CMKTest):
    def test_1(self):
        self.title('Compound')

        # ${token_price_deps}, ${compound_deps}
        self.run_model('compound-v2.pool-info', {"address": "0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4"})
        # ${token_price_deps}, compound-v2.get-comptroller
        self.run_model('compound-v2.pool-info', {"address": "0x95b4ef2869ebd94beb4eee400a99824bf5dc325b"})

        self.run_model('compound-v2.get-comptroller', {})
        self.run_model('compound-v2.get-pools', {})  # compound-v2.pool-info
        # compound-v2.pool-info, compound-v2.get-pools, ${token_price_deps}
        self.run_model('compound-v2.all-pools-info', {})

        # self.run_model('compound-v2.pool-value-historical', {"date_range": ["2021-12-15", "2021-12-18"], "token": {"address":"0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4"}}) # ${token_price_deps},compound-v2.get-comptroller,compound-v2.pool-info,compound-v2.pool-value,compound-v2.all-pools-values
        # self.run_model('compound-v2.pool-value-historical', {"date_range": ["2021-09-15", "2021-09-20"], "token": {"address":"0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4"}}) # ${token_price_deps},compound-v2.get-comptroller,compound-v2.pool-info,compound-v2.pool-value,compound-v2.all-pools-values
        # self.run_model('compound-v2.pool-value-historical', {"date_range": ["2022-01-15", "2022-01-18"], "token": {"address":"0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4"}}) # ${token_price_deps},compound-v2.get-comptroller,compound-v2.pool-info,compound-v2.pool-value,compound-v2.all-pools-values

        # cCOMP 0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4
        self.run_model('compound-v2.pool-info', {"address": "0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4"})

        # cUSDC 0x39aa39c021dfbae8fac545936693ac917d5e7563
        self.run_model('compound-v2.pool-info', {"address": "0x39aa39c021dfbae8fac545936693ac917d5e7563"})

        # cDAI 0x5d3a536e4d6dbd6114cc1ead35777bab948e3643
        self.run_model('compound-v2.pool-info', {"address": "0x5d3a536e4d6dbd6114cc1ead35777bab948e3643"})

    def test_2(self):
        self.run_model('compound-v2.all-pools-info', {}, block_number=12770589)

        self.run_model('compound-v2.all-pools-portfolio', {}, block_number=12770589)
