echo_cmd ""
echo_cmd "Run Chainlink cases:"
echo_cmd ""

test_model 0 chainlink.price-by-ens '{"domain":"eth-usd.data.eth"}' # chainlink.price-by-feed
test_model 0 chainlink.price-by-ens '{"domain":"comp-eth.data.eth"}'
test_model 0 chainlink.price-by-ens '{"domain":"avax-usd.data.eth"}'
test_model 0 chainlink.price-by-ens '{"domain":"bnb-usd.data.eth"}'
test_model 0 chainlink.price-by-ens '{"domain":"sol-usd.data.eth"}'

# AAVE 0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9
test_model 0 chainlink.price-by-registry '{"base":"0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9","quote":"0x0000000000000000000000000000000000000348"}'
test_model 0 chainlink.price-by-registry '{"base":"0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9","quote":"0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"}'

test_model 0 price.quote '{"symbol":"AAVE"}'
test_model 0 price.quote '{"symbol":"WETH"}'
test_model 0 price.quote '{"symbol":"WBTC"}'
test_model 0 price.quote '{"address":"0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"}'
test_model 0 price.quote '{"address":"0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"}'
test_model 0 price.quote '{"address":"0xD31a59c85aE9D8edEFeC411D448f90841571b89c"}'
