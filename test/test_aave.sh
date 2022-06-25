echo_cmd ""
echo_cmd "Run Aave V2 Examples:"
echo_cmd ""

test_model 0 aave-v2.get-oracle-price '{"symbol":"AAVE"}'
test_model 0 aave-v2.get-price-oracle '{}'
test_model 0 aave-v2.get-lending-pool-providers-from-registry '{}'
test_model 0 aave-v2.token-asset '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}' aave-v2.get-lending-pool,aave-v2.get-lending-pool-provider
test_model 0 aave-v2.token-asset '{"symbol":"USDC"}'
test_model 0 aave-v2.token-asset '{"symbol":"DAI"}'
test_model 0 aave-v2.lending-pool-assets '{}' aave-v2.token-asset
# 0xE41d2489571d322189246DaFA5ebDe1F4699F498: ZRX
test_model 0 aave-v2.token-liability '{"address":"0xE41d2489571d322189246DaFA5ebDe1F4699F498"}'
test_model 0 aave-v2.token-liability '{"symbol":"USDC"}'
test_model 0 aave-v2.overall-liabilities-portfolio '{}' aave-v2.token-liability
# 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48: USDC

block_number_backup=${block_number}
block_number=' -b 12770589'

test_model 0 aave-v2.lending-pool-assets '{}'

block_number=${block_number_backup}