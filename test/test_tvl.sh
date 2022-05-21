echo_cmd ""
echo_cmd "Run TVL Examples"
echo_cmd ""

curve_pool_info_tvl=curve-fi.pool-info,chainlink.price-usd,token.price,chainlink.price-by-registry,curve-fi.price-3crv

test_model 0 curve-fi.pool-info '{"address":"0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"}'
test_model 0 curve-fi.pool-info-tvl '{"address":"0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"}' ${curve_pool_info_tvl}
test_model 0 curve-fi.price-3crv '{}' ${curve_pool_info_tvl}

test_model 0 curve-fi.pool-info-tvl '{"address":"0xDC24316b9AE028F1497c275EB9192a3Ea0f67022"}' ${curve_pool_info_tvl}
test_model 0 curve-fi.pool-info-tvl '{"address":"0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"}' ${curve_pool_info_tvl}
test_model 0 curve-fi.pool-info-tvl '{"address":"0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B"}' ${curve_pool_info_tvl}
test_model 0 curve-fi.pool-info-tvl '{"address":"0xCEAF7747579696A2F0bb206a14210e3c9e6fB269"}' ${curve_pool_info_tvl}
test_model 0 curve-fi.pool-info-tvl '{"address":"0xD51a44d3FaE010294C616388b506AcdA1bfAAE46"}' ${curve_pool_info_tvl}
test_model 0 curve-fi.pool-info-tvl '{"address":"0xCEAF7747579696A2F0bb206a14210e3c9e6fB269"}' ${curve_pool_info_tvl}
test_model 0 curve-fi.pool-info-tvl '{"address":"0x5a6A4D54456819380173272A5E8E9B9904BdF41B"}' ${curve_pool_info_tvl}
test_model 0 curve-fi.pool-info-tvl '{"address":"0x93054188d876f558f4a66B2EF1d97d16eDf0895B"}' ${curve_pool_info_tvl}
test_model 0 curve-fi.pool-info-tvl '{"address":"0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF"}' ${curve_pool_info_tvl}
test_model 0 curve-fi.pool-info-tvl '{"address":"0x9D0464996170c6B9e75eED71c68B99dDEDf279e8"}' ${curve_pool_info_tvl}
test_model 1 curve-fi.pool-info-tvl '{"address":"0xd658A338613198204DCa1143Ac3F01A722b5d94A"}' ${curve_pool_info_tvl}

echo_cmd ""
echo_cmd "Run TVL Historical cases"
echo_cmd ""
test_model 0 historical.pool-info-tvl '{"address":"0xDC24316b9AE028F1497c275EB9192a3Ea0f67022","tvl_model_slug":"curve-fi.pool-info-tvl","window":"100 days"}' ${curve_pool_info_tvl}
test_model 0 historical.pool-info-tvl '{"address":"0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7","tvl_model_slug":"curve-fi.pool-info-tvl","window":"100 days"}' ${curve_pool_info_tvl}
test_model 0 historical.pool-info-tvl '{"address":"0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B","tvl_model_slug":"curve-fi.pool-info-tvl","window":"100 days"}' ${curve_pool_info_tvl}
test_model 0 historical.pool-info-tvl '{"address":"0xCEAF7747579696A2F0bb206a14210e3c9e6fB269","tvl_model_slug":"curve-fi.pool-info-tvl","window":"100 days"}' ${curve_pool_info_tvl}
test_model 0 historical.pool-info-tvl '{"address":"0xD51a44d3FaE010294C616388b506AcdA1bfAAE46","tvl_model_slug":"curve-fi.pool-info-tvl","window":"100 days"}' ${curve_pool_info_tvl}
test_model 0 historical.pool-info-tvl '{"address":"0xCEAF7747579696A2F0bb206a14210e3c9e6fB269","tvl_model_slug":"curve-fi.pool-info-tvl","window":"100 days"}' ${curve_pool_info_tvl}
test_model 0 historical.pool-info-tvl '{"address":"0x5a6A4D54456819380173272A5E8E9B9904BdF41B","tvl_model_slug":"curve-fi.pool-info-tvl","window":"100 days"}' ${curve_pool_info_tvl}
test_model 0 historical.pool-info-tvl '{"address":"0x93054188d876f558f4a66B2EF1d97d16eDf0895B","tvl_model_slug":"curve-fi.pool-info-tvl","window":"100 days"}' ${curve_pool_info_tvl}
test_model 0 historical.pool-info-tvl '{"address":"0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF","tvl_model_slug":"curve-fi.pool-info-tvl","window":"100 days"}' ${curve_pool_info_tvl}
test_model 0 historical.pool-info-tvl '{"address":"0x9D0464996170c6B9e75eED71c68B99dDEDf279e8","tvl_model_slug":"curve-fi.pool-info-tvl","window":"100 days"}' ${curve_pool_info_tvl}
test_model 1 historical.pool-info-tvl '{"address":"0xd658A338613198204DCa1143Ac3F01A722b5d94A","tvl_model_slug":"curve-fi.pool-info-tvl","window":"100 days"}' ${curve_pool_info_tvl}

# UniV3
# 0x5777d92f208679db4b9778590fa3cab3ac9e2168 (DAI/USDC)
# 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640 (USDC/WETH)
# 0x3416cf6c708da44db2624d63ea0aaef7113527c6 (USDC/USDT)
# 0x7379e81228514a1d2a6cf7559203998e20598346 (WETH/sETH2)

# Sushi
# 0x055475920a8c93CfFb64d039A8205F7AcC7722d3 OHM/DAI
echo_cmd ""
echo_cmd "Run TVL and Volume:"
echo_cmd ""
test_model 0 contrib.curve-get-tvl-and-volume '{"address":"0x9D0464996170c6B9e75eED71c68B99dDEDf279e8"}'
test_model 0 contrib.uni-sushi-get-tvl-and-volume '{"address":"0x055475920a8c93CfFb64d039A8205F7AcC7722d3"}'
test_model 0 contrib.uni-sushi-get-tvl-and-volume '{"address":"0x5777d92f208679db4b9778590fa3cab3ac9e2168"}'
test_model 0 contrib.uni-sushi-get-tvl-and-volume '{"address":"0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"}'
test_model 0 contrib.uni-sushi-get-tvl-and-volume '{"address":"0x3416cf6c708da44db2624d63ea0aaef7113527c6"}'
test_model 0 contrib.uni-sushi-get-tvl-and-volume '{"address":"0x7379e81228514a1d2a6cf7559203998e20598346"}'