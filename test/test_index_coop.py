# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestIndexCoop(CMFTest):
    def test_2022_789(self):
        """
        credmark-dev run indexcoop.fee-month -i \
            '{"address": "0x1494ca1f11d487c2bbe4543e90080aeba4ba3c2b", "year": 2022, "month": 8, "streaming_rate": 0.0095, "coop_streaming_rate": 0.7, "mint_redeem_rate": 0, "coop_mint_redeem_rate": 0}' \
            --api_url=http://localhost:8700 -j

        credmark-dev run indexcoop.fee-month -i \
            '{"address": "0x72e364f2abdc788b7e918bc238b21f109cd634d7", "year": 2022, "month": 8, "streaming_rate": 0.0095, "coop_streaming_rate": 1.0, "mint_redeem_rate": 0, "coop_mint_redeem_rate": 0}' \
            --api_url=http://localhost:8700 -j

        credmark-dev run indexcoop.fee-month -i \
            '{"address": "0x33d63ba1e57e54779f7ddaeaa7109349344cf5f1", "year": 2022, "month": 8, "streaming_rate": 0.0095, "coop_streaming_rate": 0.7, "mint_redeem_rate": 0, "coop_mint_redeem_rate": 0}' \
            --api_url=http://localhost:8700 -j

        credmark-dev run indexcoop.fee-month -i \
            '{"address": "0x2af1df3ab0ab157e1e2ad8f88a7d04fbea0c7dc6", "year": 2022, "month": 8, "streaming_rate": 0.0025, "coop_streaming_rate": 0.5, "mint_redeem_rate": 0, "coop_mint_redeem_rate": 0}' \
            --api_url=http://localhost:8700 -j

        credmark-dev run indexcoop.fee-month -i \
            '{"address": "0x47110d43175f7f2c2425e7d15792acc5817eb44f", "year": 2022, "month": 8, "streaming_rate": 0.0195, "coop_streaming_rate": 0.6, "mint_redeem_rate": 0, "coop_mint_redeem_rate": 0}' \
            --api_url=http://localhost:8700 -j

        credmark-dev run indexcoop.fee-month -i \
            '{"address": "0xaa6e8127831c9de45ae56bb1b0d4d4da6e5665bd", "year": 2022, "month": 8, "streaming_rate": 0.0195, "coop_streaming_rate": 0.6, "mint_redeem_rate": 0.001, "coop_mint_redeem_rate": 0.6}' \
            --api_url=http://localhost:8700 -j

        credmark-dev run indexcoop.fee-month -i \
            '{"address": "0x0b498ff89709d3838a063f1dfa463091f9801c2b", "year": 2022, "month": 8, "streaming_rate": 0.0195, "coop_streaming_rate": 0.6, "mint_redeem_rate": 0.001, "coop_mint_redeem_rate": 0.6}' \
            --api_url=http://localhost:8700 -j
        """

        for contract_config in [
            {"address": "0x1494ca1f11d487c2bbe4543e90080aeba4ba3c2b", "streaming_rate": 0.0095,
                "coop_streaming_rate": 0.7, "mint_redeem_rate": 0, "coop_mint_redeem_rate": 0, "use_last_price": True},
            {"address": "0x72e364f2abdc788b7e918bc238b21f109cd634d7", "streaming_rate": 0.0095,
                "coop_streaming_rate": 1.0, "mint_redeem_rate": 0, "coop_mint_redeem_rate": 0, "use_last_price": True},
            {"address": "0x33d63ba1e57e54779f7ddaeaa7109349344cf5f1", "streaming_rate": 0.0095,
                "coop_streaming_rate": 0.7, "mint_redeem_rate": 0, "coop_mint_redeem_rate": 0, "use_last_price": True},
            {"address": "0x2af1df3ab0ab157e1e2ad8f88a7d04fbea0c7dc6", "streaming_rate": 0.0025,
                "coop_streaming_rate": 0.5, "mint_redeem_rate": 0, "coop_mint_redeem_rate": 0, "use_last_price": True},
            {"address": "0x47110d43175f7f2c2425e7d15792acc5817eb44f", "streaming_rate": 0.0195,
                "coop_streaming_rate": 0.6, "mint_redeem_rate": 0, "coop_mint_redeem_rate": 0, "use_last_price": True},
            {"address": "0xaa6e8127831c9de45ae56bb1b0d4d4da6e5665bd", "streaming_rate": 0.0195,
                "coop_streaming_rate": 0.6, "mint_redeem_rate": 0.001, "coop_mint_redeem_rate": 0.6, "use_last_price": True},
            {"address": "0x0b498ff89709d3838a063f1dfa463091f9801c2b", "streaming_rate": 0.0195,
                "coop_streaming_rate": 0.6, "mint_redeem_rate": 0.001, "coop_mint_redeem_rate": 0.6, "use_last_price": True},
        ]:
            for year in [2022]:
                # for month in [7, 8, 9]:
                for month in [9]:
                    self.run_model('indexcoop.fee-month', contract_config |
                                   {"year": year, "month": month}, block_number=16_000_000)

            # for start_block, end_block in [(15053226, 15253305), (15253306, 15449617), (15449618, 15649594)]:
            for start_block, end_block in [(15449618, 15649594)]:
                self.run_model('indexcoop.fee', contract_config | {"start_block": start_block}, block_number=end_block)
