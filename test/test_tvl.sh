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