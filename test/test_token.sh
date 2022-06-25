echo_cmd ""
echo_cmd "Account Examples:"
echo_cmd ""
test_model 0 account.portfolio '{"address": "0xCE017A1dcE5A15668C4299263019c017154ACE17"}'
# Working but taking long time.
# Test account 1: 0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0
# Test account 2: 0xbdfa4f4492dd7b7cf211209c4791af8d52bf5c50
# test_model 0 account.portfolio '{"address": "0xbdfa4f4492dd7b7cf211209c4791af8d52bf5c50"}'

echo_cmd ""
echo_cmd "Run Token Examples:"
echo_cmd ""

# UniswapV3 pool USDC-WETH 0x7bea39867e4169dbe237d55c8242a8f2fcdcc387
test_model 0 uniswap-v3.get-pool-info '{"address":"0x7bea39867e4169dbe237d55c8242a8f2fcdcc387"}'
test_model 0 price.quote '{"base":{"symbol": "WETH"}}' ${token_price_deps} # token.underlying-maybe,price.oracle-chainlink-maybe,price.oracle-chainlink
test_model 0 price.quote '{"base":{"symbol": "CMK"}}' ${token_price_deps}
test_model 0 price.quote '{"base":{"symbol": "AAVE"}}' ${token_price_deps}
# AAVE: 0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9
test_model 0 price.quote '{"base":{"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9"}}' ${token_price_deps}
test_model 0 price.quote '{"base":{"symbol": "USDC"}}' ${token_price_deps}
test_model 0 price.quote '{"base":{"symbol": "MKR"}}' ${token_price_deps}
# Ampleforth: 0xd46ba6d942050d489dbd938a2c909a5d5039a161
test_model 0 price.quote '{"base":{"address": "0xd46ba6d942050d489dbd938a2c909a5d5039a161"}}' ${token_price_deps}
# RenFil token: 0xD5147bc8e386d91Cc5DBE72099DAC6C9b99276F5
test_model 0 price.quote '{"base":{"address": "0xD5147bc8e386d91Cc5DBE72099DAC6C9b99276F5"}}' ${token_price_deps}

test_model 0 token.holders '{"symbol": "CMK"}'
test_model 0 token.swap-pools '{"symbol":"CMK"}'
test_model 0 token.info '{"symbol":"CMK"}'
test_model 0 token.info '{"address":"0x019Ff0619e1D8Cd2d550940eC743fDE6d268AfE2"}'
test_model 0 token.info '{"address":"0x019ff0619e1d8cd2d550940ec743fde6d268afe2"}'

# WETH-DAI pool: https://analytics.sushi.com/pairs/0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f
test_model 0 token.swap-pool-volume '{"address":"0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f"}'
# UniSwap V3 factory: 0x1F98431c8aD98523631AE4a59f267346ea31F984
test_model 0 token.categorized-supply '{"categories": [{"accounts": {"accounts": [{"address": "0x1F98431c8aD98523631AE4a59f267346ea31F984"}]}, "categoryName": "", "categoryType": "", "circulating": true}], "token": {"symbol": "DAI"}}'

test_model 0 account.position-in-curve '{"address":"0x5291fBB0ee9F51225f0928Ff6a83108c86327636"}' # account.token-erc20
test_model 0 account.portfolio '{"address":"0x5291fBB0ee9F51225f0928Ff6a83108c86327636"}'
test_model 0 account.portfolio-aggregate '{"accounts": [{"address":"0x5291fBB0ee9F51225f0928Ff6a83108c86327636"}, {"address":"0xAE5B61a270e77F41b99965B171e20DFA8642E0Ea"}]'

test_model 0 account.var '{"address":"0x5291fBB0ee9F51225f0928Ff6a83108c86327636", "window": "3 days", "interval": 1, "confidence": 0.01}'
