
from cmf_test import CMFTest

# ImmutableModel
# CachePolicy
# IncrementalModel


class TestModels(CMFTest):
    def test_immutable(self):
        # 0x388C818CA8B9251b393131C08a736A67ccB19297 was deployed on 13834805

        self.run_model('token.deployment',
                       {"address": "0x388C818CA8B9251b393131C08a736A67ccB19297"},
                       block_number=13834805,
                       exit_code=3
                       )

        self.run_model('token.deployment',
                       {"address": "0x388C818CA8B9251b393131C08a736A67ccB19297"},
                       block_number=12834805,
                       exit_code=3
                       )

        self.run_model('token.deployment',
                       {"address": "0x388C818CA8B9251b393131C08a736A67ccB19297"},
                       block_number=14834805,
                       )

        self.run_model('token.deployment',
                       {"address": "0x388C818CA8B9251b393131C08a736A67ccB19297"},
                       block_number=14834806,
                       )

        self.run_model('token.deployment',
                       {"address": "0x388C818CA8B9251b393131C08a736A67ccB19297"},
                       block_number=14834804,
                       exit_code=3
                       )
