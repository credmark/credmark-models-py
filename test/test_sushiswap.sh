echo_cmd ""
echo_cmd "Run SushiSwap Examples:"
echo_cmd ""
test_model 0 sushiswap.get-weighted-price '{"symbol": "USDC"}'
test_model 0 sushiswap.get-weighted-price '{"symbol": "AAVE"}'
test_model 0 sushiswap.get-weighted-price '{"symbol": "DAI"}'
test_model 0 sushiswap.get-weighted-price '{"symbol": "WETH"}'
test_model 0 sushiswap.get-weighted-price '{"symbol": "MKR"}'
test_model 0 sushiswap.all-pools '{}'
test_model 0 sushiswap.get-pool '{"token0":{"symbol":"DAI"}, "token1":{"symbol":"WETH"}}'
test_model 0 sushiswap.get-pool-info '{"address":"0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"}'
test_model 0 sushiswap.get-pools '{"address":"0x68CFb82Eacb9f198d508B514d898a403c449533E"}' # CMK_ADDRESS
