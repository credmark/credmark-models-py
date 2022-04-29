echo_cmd ""
echo_cmd "Run Uniswap Examples:"
echo_cmd ""
test_model 0 uniswap.tokens '{}'
test_model 0 uniswap.exchange '{}'
test_model 0 uniswap.quoter-price-usd '{"tokenAddress":"0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"}'
test_model 0 uniswap.router-price-usd '{}'

echo_cmd ""
echo_cmd "Run Uniswap V2 Examples:"
echo_cmd ""
test_model 0 uniswap-v2.get-weighted-price '{"symbol": "USDC"}'
test_model 0 uniswap-v2.get-weighted-price '{"symbol": "AAVE"}'
test_model 0 uniswap-v2.get-weighted-price '{"symbol": "DAI"}'
test_model 0 uniswap-v2.get-weighted-price '{"symbol": "WETH"}'
test_model 0 uniswap-v2.get-weighted-price '{"symbol": "MKR"}'
# 0xD533a949740bb3306d119CC777fa900bA034cd52: Curve DAO Token (CRV)
test_model 0 uniswap-v2.get-pools '{"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}'
# Uniswap ETH/CRV LP (UNI-V2)
test_model 0 uniswap-v2.pool-volume '{"address": "0x3da1313ae46132a397d90d95b1424a9a7e3e0fce"}'


echo_cmd ""
echo_cmd "Run Uniswap V3 Examples:"
echo_cmd ""
# TODO: USDC price wrong from USDC/DAI pool
test_model 0 uniswap-v3.get-weighted-price '{"symbol": "USDC"}' uniswap-v3.get-pool-info
test_model 0 uniswap-v3.get-weighted-price '{"symbol": "AAVE"}' uniswap-v3.get-pool-info
test_model 0 uniswap-v3.get-weighted-price '{"symbol": "DAI"}' uniswap-v3.get-pool-info
test_model 0 uniswap-v3.get-weighted-price '{"symbol": "WETH"}' uniswap-v3.get-pool-info
test_model 0 uniswap-v3.get-weighted-price '{"symbol": "MKR"}' uniswap-v3.get-pool-info
test_model 0 uniswap-v3.get-weighted-price '{"symbol": "CMK"}' uniswap-v3.get-pool-info
test_model 0 uniswap-v3.get-pools '{"symbol": "MKR"}'
# WETH/CMK pool: 0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3
test_model 0 uniswap-v3.get-pool-info '{"address": "0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3"}'
