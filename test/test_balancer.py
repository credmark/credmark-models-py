# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestBalancer(CMFTest):
    def test_pool_info(self):
        self.title('Balancer - Pool Info')
        self.run_model('balancer-fi.get-pool-price-info', {"address": "0x32296969Ef14EB0c6d29669C550D4a0449130230"})
        self.run_model('balancer-fi.get-pool-price-info', {"address": "0x647c1FD457b95b75D0972fF08FE01d7D7bda05dF"})
