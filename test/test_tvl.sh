echo_cmd ""
echo_cmd "Run TVL Examples"
echo_cmd ""

curve_pool_info_tvl=curve-fi.pool-info,price.quote,chainlink.price-by-registry

test_model 0 curve-fi.pool-info '{"address":"0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"}'
test_model 0 curve-fi.pool-info-tvl '{"address":"0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"}' ${curve_pool_info_tvl}

curve_pools="0xDC24316b9AE028F1497c275EB9192a3Ea0f67022 \
0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7 \
0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B \
0xCEAF7747579696A2F0bb206a14210e3c9e6fB269 \
0xD51a44d3FaE010294C616388b506AcdA1bfAAE46 \
0x5a6A4D54456819380173272A5E8E9B9904BdF41B \
0x93054188d876f558f4a66B2EF1d97d16eDf0895B \
0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF \
0x9D0464996170c6B9e75eED71c68B99dDEDf279e8 \
0xd658A338613198204DCa1143Ac3F01A722b5d94A"

for pool_addr in $curve_pools; do
    test_model 0 curve-fi.pool-info-tvl '{"address":"'$pool_addr'"}' ${curve_pool_info_tvl}
done

echo_cmd ""
echo_cmd "Run TVL Historical cases"
echo_cmd ""

for pool_addr in $curve_pools; do
    # credmark-dev run historical.run-model -i '{"model_slug":"curve-fi.pool-info-tvl","model_input":{"address":"'$pool_addr'"},"window":"280 days","interval":"1 day"}' --api_url=http://localhost:8700
    test_model 0 historical.run-model '{"model_slug":"curve-fi.pool-info-tvl","model_input":{"address":"'$pool_addr'"},"window":"20 days","interval":"1 day"}' ${curve_pool_info_tvl}
done

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

pools="0x055475920a8c93CfFb64d039A8205F7AcC7722d3
       0x5777d92f208679db4b9778590fa3cab3ac9e2168
       0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640
       0x3416cf6c708da44db2624d63ea0aaef7113527c6
       0x7379e81228514a1d2a6cf7559203998e20598346"
for pool in $pools; do
    test_model 0 contrib.uni-sushi-get-tvl-and-volume '{"address":"'${pool}'"}'
done