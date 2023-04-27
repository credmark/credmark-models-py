# pylint:disable=locally-disabled,line-too-long,unsubscriptable-object,assignment-from-none

from cmf_test import CMFTest


class TestIPOR(CMFTest):
    def test(self):
        self.title('IPOR')

        self.run_model('ipor.get-oracle-and-calculator',
                       {}, block_number=16812845)
        self.run_model('ipor.get-index', {}, block_number=16812845)
        self.run_model('ipor.get-lp-exchange', {}, block_number=16812845)

        result = self.run_model_with_output(
            'ipor.get-swap',
            {"timestamp": 1676688179,
                "asset": "0x6B175474E89094C44Da98b954EedeAC495271d0F", "notional": 1000000},
            block_number=16652629)

        self.assertAlmostEqual(
            result['output']['payFixedPayoff'], 0.000000000000000000, places=18)
        self.assertAlmostEqual(
            result['output']['receiveFixedPayoff'], 0.000000000000000000, places=18)

        result = self.run_model_with_output(
            'ipor.get-swap',
            {"timestamp": 1676523767,
                "asset": "0x6B175474E89094C44Da98b954EedeAC495271d0F", "notional": 1000000},
            block_number=16639079)

        self.assertAlmostEqual(
            result['output']['payFixedPayoff'], 0.000000000000000000, places=18)
        self.assertAlmostEqual(
            result['output']['receiveFixedPayoff'], 1e-18, places=18)
