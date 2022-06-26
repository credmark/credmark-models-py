echo_cmd ""
echo_cmd "Run CMK"
echo_cmd ""
test_model 0 cmk.total-supply '{}'
test_model 0 cmk.circulating-supply '{"message":"hello world"}'
test_model 0 xcmk.cmk-staked '{}'
test_model 0 xcmk.total-supply '{}'
test_model 0 xcmk.deployment-time '{}'
test_model 0 cmk.vesting-contracts '{}'
test_model 0 cmk.get-all-vesting-balances '{}'
test_model 0 cmk.get-vesting-accounts '{}'

echo Below test do not work with web3 node running on the gateway
test_model 0 cmk.get-vesting-info-by-account '{"address":"0xd766ee3ab3952fe7846db899ce0139da06fbe459"}'
test_model 0 cmk.get-vesting-info-by-account '{"address":"0x84d12110D00266Ae41EF064c8B933802d0fc3618"}'
test_model 0 cmk.get-vesting-info-by-account '{"address":"0x2DA5e2C09d4DEc83C38Db2BBE2c1Aa111dDEe028"}'
test_model 0 cmk.get-vesting-info-by-account '{"address":"0x6395d77c5fd4ab21c442292e25a92be89ff29aa9"}'
test_model 0 cmk.vesting-events '{"address":"0xC2560D7D2cF12f921193874cc8dfBC4bb162b7cb"}'