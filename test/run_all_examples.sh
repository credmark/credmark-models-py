#!/bin/bash

credmark-dev list
echo ""
echo "Neil's example:"
echo ""
credmark-dev run contrib.neilz --input '{}' -b 14234904 --format_json
echo ""
echo "Examples"
echo ""
credmark-dev run example.all --input '{}' -l example.contract,example.ledger-transactions,example.block-time -b 14234904 --format_json
credmark-dev run example.model --input '{}' -b 14234904 --format_json
credmark-dev run example.model-run --input '{}' -b 14234904 --format_json
credmark-dev run example.contract --input '{}' -b 14234904 --format_json
credmark-dev run example.data-error-1 --input '{}' -b 14234904 --format_json
credmark-dev run example.data-error-2 --input '{}' -b 14234904 --format_json
credmark-dev run example.block-time --input '{}' -b 14234904 --format_json
credmark-dev run example.block-number --input '{}' -b 14234904 --format_json
credmark-dev run example.address --input '{}' -b 14234904 --format_json
credmark-dev run example.libraries --input '{}' -b 14234904 --format_json
credmark-dev run example.token --input '{}' -b 14234904 --format_json
credmark-dev run example.dto --input '{}' -b 14234904 --format_json
credmark-dev run example.dto-type-test-1 --input '{"positions": [{"amount": "4.2", "asset": {"symbol": "USDC"}},{"amount": "4.4", "asset": {"symbol": "USDT"}}]}' -b 14234904 --format_json
credmark-dev run example.dto-type-test-2 --input '{"positions": [{"amount": "4.2", "asset": {"symbol": "USDC"}},{"amount": "4.4", "asset": {"symbol": "USDT"}}]}' -b 14234904 --format_json
credmark-dev run example.account --input '{}' -b 14234904 --format_json
credmark-dev run example.ledger-aggregates --input '{}' -b 14234904 --format_json
echo ""
echo "Run CMK"
echo ""
credmark-dev run cmk.total-supply --input '{}' -b 14234904 --format_json
credmark-dev run cmk.circulating-supply --input '{"message":"hello world"}' -b 14234904 --format_json
credmark-dev run xcmk.cmk-staked --input '{}' -b 14234904 --format_json
credmark-dev run xcmk.total-supply --input '{}' -b 14234904 --format_json
credmark-dev run xcmk.deployment-time --input '{}' -b 14234904 --format_json
credmark-dev run cmk.vesting-contracts --input '{}' -b 14234904 --format_json
credmark-dev run cmk.get-all-vesting-balances --input '{}' -l cmk.get-vesting-accounts -b 14234904 --format_json
credmark-dev run cmk.get-vesting-accounts --input '{}' -b 14234904 --format_json
credmark-dev run cmk.get-vesting-info-by-account --input '{"address":"0x6395d77c5fd4ab21c442292e25a92be89ff29aa9"}' -b 14234904 --format_json
credmark-dev run cmk.vesting-events --input '{"address":"0xC2560D7D2cF12f921193874cc8dfBC4bb162b7cb"}' -b 14234904 --format_json
echo ""
echo "Account Examples:"
echo ""
credmark-dev run account.portfolio --input '{"address": "0xCE017A1dcE5A15668C4299263019c017154ACE17"}' -b 14234904 --format_json
echo ""
echo "Run Historical Examples:"
echo ""
credmark-dev run example.historical --input '{"model_slug":"token.price-ext","model_input":{"symbol": "USDC"}}' -l token.price-ext -b 14234904 --format_json
credmark-dev run example.historical --input '{"model_slug":"token.price","model_input":{"symbol": "USDC"}}' -l token.price -b 14234904 --format_json
credmark-dev run example.historical --input '{"model_slug":"token.overall-volume","model_input":{"symbol": "USDC"}}' -l token.overall-volume -b 14234904 --format_json
credmark-dev run example.historical-block --input '{}' -l example.libraries -b 14234904 --format_json
echo ""
echo "Run Ledger Examples:"
echo ""
credmark-dev run example.ledger-token-transfers --input '{"address":"0x3812D217bB3A0B43aa16985A616A4e0c6A17C65F"}' -b 14234904 --format_json
credmark-dev run example.ledger-transactions --input '{}' -b 14234904 --format_json
credmark-dev run example.ledger-receipts --input '{}' -b 14234904 --format_json
credmark-dev run example.ledger-traces --input '{}' -b 14234904 --format_json
credmark-dev run example.ledger-blocks --input '{}' -b 14234904 --format_json
credmark-dev run example.ledger-tokens --input '{}' -b 14234904 --format_json
credmark-dev run example.ledger-contracts --input '{}' -b 14234904 --format_json
credmark-dev run example.ledger-logs --input '{}' -b 14234904 --format_json
echo ""
echo "Run Iteration Examples:"
echo ""
credmark-dev run example.iteration --input '{}' -b 14234904 --format_json
echo ""
echo "Run Token Examples:"
echo ""
credmark-dev run token.price --input '{"symbol": "WETH"}' -l token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"symbol": "CMK"}' -l token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"symbol": "AAVE"}' -l token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9"}' -l token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"symbol": "USDC"}' -l token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"symbol": "MKR"}' -l token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"address": "0xd46ba6d942050d489dbd938a2c909a5d5039a161"}' -l token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"address": "0xD5147bc8e386d91Cc5DBE72099DAC6C9b99276F5"}' -l token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price-ext --input '{"symbol": "CMK"}' -l token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.holders --input '{"symbol": "CMK"}' -b 14234904 --format_json
credmark-dev run token.swap-pools --input '{"symbol":"CMK"}' -b 14234904 --format_json
credmark-dev run token.info --input '{"symbol":"CMK"}' -b 14234904 --format_json
credmark-dev run token.info --input '{"address":"0x019Ff0619e1D8Cd2d550940eC743fDE6d268AfE2"}' -b 14234904 --format_json
credmark-dev run token.info --input '{"address":"0x019ff0619e1d8cd2d550940ec743fde6d268afe2"}' -b 14234904 --format_json
credmark-dev run token.swap-pool-volume --input '{"address":"0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f"}' -b 14234904 --format_json
credmark-dev run token.categorized-supply --input '{"categories": [{"accounts": {"accounts": [{"address": "0x1F98431c8aD98523631AE4a59f267346ea31F984"}]}, "categoryName": "", "categoryType": "", "circulating": true}], "token": {"symbol": "DAI"}}' -b 14234904 --format_json
echo ""
echo "Run Compound Examples:"
echo ""
credmark-dev run compound-v2.get-pool-info --input '{"address":"0x95b4ef2869ebd94beb4eee400a99824bf5dc325b"}' -l token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price,compound-v2.get-comptroller -b 14234904 --format_json
credmark-dev run compound-v2.get-comptroller --input '{}' -b 14234904 --format_json
credmark-dev run compound-v2.get-pools --input '{}' -l compound-v2.get-pool-info -b 14234904 --format_json
credmark-dev run compound-v2.all-pools-info --input '{}' -l compound-v2.get-pool-info,compound-v2.get-pools,token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run compound-v2.pool-value-historical --input '{"date_range": ["2021-12-15", "2021-12-18"], "token": {"address":"0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4"}}' -l token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price,compound-v2.get-comptroller,compound-v2.get-pool-info,compound-v2.pool-value -b 14234904 --format_json
credmark-dev run compound-v2.pool-value-historical --input '{"date_range": ["2021-09-15", "2021-09-20"], "token": {"address":"0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4"}}' -l token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price,compound-v2.get-comptroller,compound-v2.get-pool-info,compound-v2.pool-value -b 14234904 --format_json
credmark-dev run compound-v2.pool-value-historical --input '{"date_range": ["2022-01-15", "2022-01-18"], "token": {"address":"0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4"}}' -l token.price,token.price-ext,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price,compound-v2.get-comptroller,compound-v2.get-pool-info,compound-v2.pool-value -b 14234904 --format_json
echo ""
echo "Run Uniswap Examples:"
echo ""
credmark-dev run uniswap.tokens --input '{}' -b 14234904 --format_json
credmark-dev run uniswap.exchange --input '{}' -b 14234904 --format_json
credmark-dev run uniswap.quoter-price-usd --input '{"tokenAddress":"0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"}' -b 14234904 --format_json
credmark-dev run uniswap.router-price-usd --input '{}' -b 14234904 --format_json
echo ""
echo "Run Uniswap V2 Examples:"
echo ""
credmark-dev run uniswap-v2.get-average-price --input '{"symbol": "USDC"}' -b 14234904 --format_json
credmark-dev run uniswap-v2.get-average-price --input '{"symbol": "AAVE"}' -b 14234904 --format_json
credmark-dev run uniswap-v2.get-average-price --input '{"symbol": "DAI"}' -b 14234904 --format_json
credmark-dev run uniswap-v2.get-average-price --input '{"symbol": "WETH"}' -b 14234904 --format_json
credmark-dev run uniswap-v2.get-average-price --input '{"symbol": "MKR"}' -b 14234904 --format_json
credmark-dev run uniswap-v2.get-pools --input '{"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}' -b 14234904 --format_json
credmark-dev run uniswap-v2.pool-volume --input '{"address": "0x3da1313ae46132a397d90d95b1424a9a7e3e0fce"}' -b 14234904 --format_json
echo ""
echo "Run Uniswap V3 Examples:"
echo ""
credmark-dev run uniswap-v3.get-average-price --input '{"symbol": "USDC"}' -b 14234904 --format_json
credmark-dev run uniswap-v3.get-average-price --input '{"symbol": "AAVE"}' -b 14234904 --format_json
credmark-dev run uniswap-v3.get-average-price --input '{"symbol": "DAI"}' -b 14234904 --format_json
credmark-dev run uniswap-v3.get-average-price --input '{"symbol": "WETH"}' -b 14234904 --format_json
credmark-dev run uniswap-v3.get-average-price --input '{"symbol": "MKR"}' -b 14234904 --format_json
credmark-dev run uniswap-v3.get-pools --input '{"symbol": "MKR"}' -b 14234904 --format_json
credmark-dev run uniswap-v3.get-pool-info --input '{"address": "0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3"}' -b 14234904 --format_json
credmark-dev run uniswap-v3.get-average-price --input '{"symbol": "CMK"}' -b 14234904 --format_json
echo ""
echo "Run SushiSwap Examples:"
echo ""
credmark-dev run sushiswap.get-average-price --input '{"symbol": "USDC"}' -b 14234904 --format_json
credmark-dev run sushiswap.get-average-price --input '{"symbol": "AAVE"}' -b 14234904 --format_json
credmark-dev run sushiswap.get-average-price --input '{"symbol": "DAI"}' -b 14234904 --format_json
credmark-dev run sushiswap.get-average-price --input '{"symbol": "WETH"}' -b 14234904 --format_json
credmark-dev run sushiswap.get-average-price --input '{"symbol": "MKR"}' -b 14234904 --format_json
credmark-dev run sushiswap.all-pools --input '{}' -b 14234904 --format_json
credmark-dev run sushiswap.get-pool --input '{"token0":{"symbol":"DAI"}, "token1":{"symbol":"WETH"}}' -b 14234904 --format_json
credmark-dev run sushiswap.get-pool-info --input '{"address":"0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"}' -b 14234904 --format_json
credmark-dev run sushiswap.get-pools --input '{"address":"0x68CFb82Eacb9f198d508B514d898a403c449533E"}' -b 14234904 --format_json
echo ""
echo "Run Aave V2 Examples:"
echo ""
credmark-dev run aave-v2.token-asset --input '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}' -l aave-v2.get-lending-pool -b 14234904 --format_json
credmark-dev run aave-v2.token-asset --input '{"symbol":"USDC"}' -b 14234904 --format_json
credmark-dev run aave-v2.token-asset --input '{"symbol":"DAI"}' -b 14234904 --format_json
credmark-dev run aave-v2.lending-pool-assets --input '{}' -l aave-v2.token-asset -b 14234904 --format_json
credmark-dev run aave-v2.token-liability --input '{"address":"0xE41d2489571d322189246DaFA5ebDe1F4699F498"}' -b 14234904 --format_json
credmark-dev run aave-v2.token-liability --input '{"symbol":"USDC"}' -b 14234904 --format_json
credmark-dev run aave-v2.overall-liabilities-portfolio --input '{}' -l aave-v2.token-liability -b 14234904 --format_json
echo ""
echo "Run Curve Examples"
echo ""
credmark-dev run curve-fi.all-pools --input '{}' -l curve-fi.get-registry -b 14234904 --format_json
credmark-dev run curve-fi.pool-info --input '{"address":"0x43b4fdfd4ff969587185cdb6f0bd875c5fc83f8c"}' -b 14234904 --format_json
credmark-dev run curve-fi.all-gauges --input '{}' -b 14234904 --format_json
credmark-dev run curve-fi.get-gauge-stake-and-claimable-rewards --input '{"address":"0x824F13f1a2F29cFEEa81154b46C0fc820677A637"}' -b 14234904 --format_json
credmark-dev run curve-fi.gauge-yield --input '{"address":"0x824F13f1a2F29cFEEa81154b46C0fc820677A637"}' -l curve-fi.get-gauge-stake-and-claimable-rewards -b 14234904 --format_json
credmark-dev run curve-fi.all-gauge-claim-addresses --input '{"address":"0x824F13f1a2F29cFEEa81154b46C0fc820677A637"}' -b 14234904 --format_json
credmark-dev run curve-fi.all-gauge-claim-addresses --input '{"address":"0x72E158d38dbd50A483501c24f792bDAAA3e7D55C"}' -b 14234904 --format_json
credmark-dev run contrib.nish-curve-get-pegging-ratio --input '{"address": "0xfd5db7463a3ab53fd211b4af195c5bccc1a03890"}' -b 14234904 --format_json
credmark-dev run contrib.nish-curve-get-pegging-ratio-historical --input '{"pool": {"address": "0xfd5db7463a3ab53fd211b4af195c5bccc1a03890"}, "date_range": ["2022-01-10","2022-01-15"]}' -b 14234904 --format_json
credmark-dev run contrib.nish-curve-get-depegging-amount --input '{"pool": {"address": "0xfd5db7463a3ab53fd211b4af195c5bccc1a03890"},"token": {"address": "0xd71ecff9342a5ced620049e616c5035f1db98620"}, "desired_ratio": 0.98485645}' -b 14234904 --format_json
echo ""
echo "Run Finance Examples"
echo ""
credmark-dev run finance.example-var-contract --input '{"asOf": "2022-02-17", "window": "30 days", "interval": 3, "confidences": [0.01,0.05]}' -l finance.example-var-contract,finance.example-historical-price,finance.var-engine-historical -b 14234904 --format_json
credmark-dev run finance.lcr --input '{"address": "0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0", "cashflow_shock": 1e10}' -b 14234904 --format_json
