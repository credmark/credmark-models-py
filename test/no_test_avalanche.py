# pylint: disable=line-too-long, pointless-string-statement
from cmf_test import CMFTest

# 56: bsc
# 137: polygon
# 10: optimism
# 42161: arbitrum
# 250: fantom
# 43114: avalanche


class TestAvalanche(CMFTest):
    def test(self):
        self.title('Avalanche')

        chain_id = 43114

        last_block_output = self.run_model_with_output(
            'chain.get-latest-block', {}, block_number=None, chain_id=chain_id)

        last_block = last_block_output['output']['blockNumber'] - 100

        self.run_model('price.oracle-chainlink',
                       {"base": "0xabc9547b534519ff73921b1fba6e672b5f58d083"},
                       block_number=last_block, chain_id=chain_id)

        # self.run_model(
        #     'aave-v2.account-info',
        #     {"address": "0x7f90122BF0700F9E7e1F688fe926940E8839F353"},
        #     chain_id=chain_id,
        #     block_number=32537910)

        # https://snowtrace.io/tx/0x83b307af18c06818619934b15ffd7083a3601a333bc60508ce42901a8edfb762
        # Curve 2 for USDC.e 0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664
        # receive avUSDC 0x46A51127C3ce23fb7AB1DE06226147F446e4a857

        """
        credmark-dev run aave-v2.account-info-reserve \
        -i '{"address": "0x7f90122BF0700F9E7e1F688fe926940E8839F353", "reserve": "0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664"}' \
        -b 32537910 -c 43114 -j --api_url http://localhost:8700
        """

        self.run_model(
            'aave-v2.account-info-reserve',
            {"address": "0x7f90122BF0700F9E7e1F688fe926940E8839F353",
                "reserve": "0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664"},
            chain_id=chain_id,
            block_number=32537910)
