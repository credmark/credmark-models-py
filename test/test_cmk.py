# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest

from models.tmp_abi_lookup import CMK_ADDRESS, STAKED_CREDMARK_ADDRESS


class TestCMK(CMFTest):
    def test(self):
        self.title('CMK')

        self.run_model('cmk.total-supply')
        self.run_model('cmk.circulating-supply', {"message": "hello world"})
        self.run_model('xcmk.cmk-staked')
        self.run_model('xcmk.total-supply')
        # self.run_model('xcmk.deployment-time')
        self.run_model('cmk.vesting-contracts')

        print('Below test do not work with web3 node running on the gateway')
        exit_code_failed = (1 if self.type in ['prod', 'gw'] else 0)
        self.run_model('cmk.get-all-vesting-balances',
                       {}, exit_code=exit_code_failed)
        self.run_model('cmk.get-vesting-accounts',
                       {}, exit_code=exit_code_failed)
        self.run_model('cmk.vesting-events', {}, exit_code=exit_code_failed)

        self.run_model('cmk.get-vesting-info-by-account',
                       {"address": "0xd766ee3ab3952fe7846db899ce0139da06fbe459"}, exit_code=exit_code_failed)
        self.run_model('cmk.get-vesting-info-by-account',
                       {"address": "0x84d12110D00266Ae41EF064c8B933802d0fc3618"}, exit_code=exit_code_failed)
        self.run_model('cmk.get-vesting-info-by-account',
                       {"address": "0x2DA5e2C09d4DEc83C38Db2BBE2c1Aa111dDEe028"}, exit_code=exit_code_failed)
        self.run_model('cmk.get-vesting-info-by-account',
                       {"address": "0x6395d77c5fd4ab21c442292e25a92be89ff29aa9"}, exit_code=exit_code_failed)

        self.run_model('price.quote',
                       {"base": STAKED_CREDMARK_ADDRESS}, block_number=17171332)

        self.run_model('price.quote',
                       {"base": CMK_ADDRESS}, block_number=17171332)
