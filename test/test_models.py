# pylint: disable=pointless-string-statement, line-too-long

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

        self.run_model('example.immutable-wrong-output', {}, exit_code=1)
        self.run_model('example.immutable', {}, block_number=100)
        self.run_model('example.immutable', {}, block_number=99, exit_code=3)

    def test_incremental(self):
        # Because model result changes from block to block, we need to test for
        # 1) completeness and
        # 2) under local model and remote model

        self.run_model('example.incremental-wrong-output', {}, exit_code=1)
        self.run_model('example.incremental', {})

        # Test for completeness
        """
        cc = Contract('0x692437de2cAe5addd26CCF6650CaD722d914d974')
        from models.tmp_abi_lookup import ICHI_VAULT, ICHI_VAULT_DEPOSIT_GUARD, ICHI_VAULT_FACTORY, UNISWAP_V3_POOL_ABI
        cc.set_abi(ICHI_VAULT, set_loaded=True)
        list(cc.fetch_events(cc.events.Withdraw, from_block=39530703, to_block=43752597, by_range=10_000)) == 6

        40174011, 41369906, 41893553, 43378778, 43676363, 43752597

        python test/test.py run contract.events-block-series -j \
        -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974", "event_name": "Withdraw", "event_abi": [{"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": true, "internalType": "address", "name": "to", "type": "address"}, {"indexed": false, "internalType": "uint256", "name": "shares", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "amount0", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "amount1", "type": "uint256"}], "name": "Withdraw", "type": "event"}]}' \
        -b 43752597 -c 137 -l - | grep output

        python test/test.py run contract.events-block-series -j \
        -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974", "event_name": "Withdraw", "event_abi": [{"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": true, "internalType": "address", "name": "to", "type": "address"}, {"indexed": false, "internalType": "uint256", "name": "shares", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "amount0", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "amount1", "type": "uint256"}], "name": "Withdraw", "type": "event"}]}' \
        -b 43752597 -c 137 -l '*' | grep output

        python test/test.py run contract.events -j \
        -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974", "event_name": "Withdraw", "event_abi": [{"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": true, "internalType": "address", "name": "to", "type": "address"}, {"indexed": false, "internalType": "uint256", "name": "shares", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "amount0", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "amount1", "type": "uint256"}], "name": "Withdraw", "type": "event"}]}' \
        -b 43752597 -c 137 -l '*' | grep n_rows

        python test/test.py run contract.events -j \
        -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974", "event_name": "Withdraw", "event_abi": [{"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": true, "internalType": "address", "name": "to", "type": "address"}, {"indexed": false, "internalType": "uint256", "name": "shares", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "amount0", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "amount1", "type": "uint256"}], "name": "Withdraw", "type": "event"}]}' \
        -b 43752597 -c 137 -l - | grep n_rows
        """

        events_result = self.run_model_with_output(
            'contract.events-block-series',
            {"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974", "event_name": "Withdraw", "event_abi": [{"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": True, "internalType": "address", "name": "to", "type": "address"}, {
                "indexed": False, "internalType": "uint256", "name": "shares", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"}], "name": "Withdraw", "type": "event"}]},
            block_number=43752597,
            chain_id=137
        )

        self.assertEqual(len(events_result['output']['series']), 6)

        # Test for local model
        # make model to run locally

    def test_cache_skip(self):
        # It skips the cache, local or model would have the same result
        # Nothing to test
        pass

    def test_cache_off_chain(self):
        # Nothing to test
        pass

    def test_cache_ignore_block(self):
        # Nothing to test
        pass
