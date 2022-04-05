#!/bin/bash

credmark-dev list
echo ""
echo "Neil's example:"
echo ""
credmark-dev run contrib.neilz --input '{}' -b 14234904 --format_json
echo ""
echo "echo Examples"
echo ""
credmark-dev run example.all --input '{}' -b 14234904 --format_json
credmark-dev run example.echo --input '{"message":"hello world"}' -b 14234904 --format_json
credmark-dev run example.contract --input '{}' -b 14234904 --format_json
credmark-dev run example.data-error --input '{}' -b 14234904 --format_json
credmark-dev run example.data-error-2 --input '{}' -b 14234904 --format_json
credmark-dev run example.block-time --input '{}' -b 14234904 --format_json
credmark-dev run example.block-number --input '{}' -b 14234904 --format_json
credmark-dev run example.address --input '{}' -b 14234904 --format_json
credmark-dev run example.type-test-1 --input '{"positions": [{"amount": "4.2", "asset": {"symbol": "USDC"}},{"amount": "4.4", "asset": {"symbol": "USDT"}}]}' -b 14234904 --format_json
credmark-dev run example.type-test-2 --input '{"positions": [{"amount": "4.2", "asset": {"symbol": "USDC"}},{"amount": "4.4", "asset": {"symbol": "USDT"}}]}' -b 14234904 --format_json
credmark-dev run example.account --input '{}' -b 14234904 --format_json
echo ""
echo "CMK Examples:"
echo ""
credmark-dev run cmk.total-supply --input '{}' -b 14234904 --format_json
credmark-dev run cmk.circulating-supply --input '{"message":"hello world"}' -b 14234904 --format_json
credmark-dev run xcmk.cmk-staked --input '{}' -b 14234904 --format_json
credmark-dev run xcmk.total-supply --input '{}' -b 14234904 --format_json
credmark-dev run xcmk.deployment-time --input '{}' -b 14234904 --format_json
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
credmark-dev run example.historical-snap --input '{}' -l example.libraries -b 14234904 --format_json
credmark-dev run example.historical-block-snap --input '{}' -l example.echo -b 14234904 --format_json
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
credmark-dev run example.token-loading --input '{}' -b 14234904 --format_json
credmark-dev run token.price --input '{"symbol": "WETH"}' -l uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"symbol": "CMK"}' -l uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"symbol": "AAVE"}' -l uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9"}' -l uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"symbol": "USDC"}' -l uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"symbol": "MKR"}' -l uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"address": "0xd46ba6d942050d489dbd938a2c909a5d5039a161"}' -l uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price --input '{"address": "0xD5147bc8e386d91Cc5DBE72099DAC6C9b99276F5"}' -l uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.price-ext --input '{"symbol": "CMK"}' -l uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run token.holders --input '{"symbol": "CMK"}' -b 14234904 --format_json
credmark-dev run token.swap-pools --input '{"symbol":"CMK"}' -b 14234904 --format_json
credmark-dev run token.info --input '{"symbol":"CMK"}' -b 14234904 --format_json
credmark-dev run token.info --input '{"address":"0x019Ff0619e1D8Cd2d550940eC743fDE6d268AfE2"}' -b 14234904 --format_json
credmark-dev run token.info --input '{"address":"0x019ff0619e1d8cd2d550940ec743fde6d268afe2"}' -b 14234904 --format_json
credmark-dev run token.swap-pool-volume --input '{"address":"0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f"}' -b 14234904 --format_json
credmark-dev run token.categorized-supply --input '{"categories": [{"accounts": {"accounts": [{"address": "0x1F98431c8aD98523631AE4a59f267346ea31F984"}]}, "categoryName": "", "categoryType": "", "circulating": true}], "token": {"symbol": "DAI"}}' -b 14234904 --format_json
echo ""
echo "Run TestRun Example:"
echo ""
credmark-dev run example.run-test --input '{"model":"price","input":{"symbol": "CMK"}}' -b 14234904 --format_json
echo ""
echo "Run Library Examples:"
echo ""
credmark-dev run example.libraries --input '{}' -b 14234904 --format_json
echo ""
echo "Run Compound Examples:"
echo ""
credmark-dev run compound.test --input '{"symbol":"DAI"}' -b 14234904 --format_json
credmark-dev run compound.get-pools --input '{}' -l compound.get-pool-info,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
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
credmark-dev run uniswap-v3.get-historical-price --input '{"token": {"symbol": "USDC"}, "window": "10 days"}' -l uniswap-v3.get-average-price -b 14234904 --format_json
credmark-dev run uniswap-v3.get-historical-price --input '{"token": {"symbol": "CMK"}, "window": "10 days", "interval":"5 days"}' -l uniswap-v3.get-average-price -b 14234904 --format_json
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
credmark-dev run aave.token-asset --input '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}' -b 14234904 --format_json
credmark-dev run aave.token-asset --input '{"symbol":"USDC"}' -b 14234904 --format_json
credmark-dev run aave.token-asset --input '{"symbol":"DAI"}' -b 14234904 --format_json
credmark-dev run aave.lending-pool-assets --input '{}' -l aave.token-asset -b 14234904 --format_json
credmark-dev run aave.token-liability --input '{"address":"0xE41d2489571d322189246DaFA5ebDe1F4699F498"}' -b 14234904 --format_json
credmark-dev run aave.token-liability --input '{"symbol":"USDC"}' -b 14234904 --format_json
credmark-dev run aave.overall-liabilities-portfolio --input '{}' -l aave.token-liability -b 14234904 --format_json
credmark-dev run aave.token-asset-historical --input '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}' -l aave.token-asset -b 14234904 --format_json
echo ""
echo "Run Curve Examples"
echo ""
credmark-dev run curve-fi.all-pools --input '{}' -l curve-fi.pool-info -b 14234904 --format_json
credmark-dev run curve-fi.pool-info --input '{"address":"0x43b4fdfd4ff969587185cdb6f0bd875c5fc83f8c"}' -b 14234904 --format_json
credmark-dev run curve-fi.pool-historical-reserve --input '{"address":"0x43b4fdfd4ff969587185cdb6f0bd875c5fc83f8c"}' -l curve-fi.pool-info -b 14234904 --format_json
credmark-dev run curve-fi.all-yield --input '{}' -l curve-fi.gauge-yield,curve-fi.pool-info,curve-fi.get-gauge-stake-and-claimable-rewards,curve-fi.all-gauge-claim-addresses -b 14234904 --format_json
credmark-dev run curve-fi.all-gauges --input '{}' -b 14234904 --format_json
credmark-dev run curve-fi.get-gauge-stake-and-claimable-rewards --input '{"address":"0x824F13f1a2F29cFEEa81154b46C0fc820677A637"}' -b 14234904 --format_json
credmark-dev run curve-fi.gauge-yield --input '{"address":"0x824F13f1a2F29cFEEa81154b46C0fc820677A637"}' -l curve-fi.get-gauge-stake-and-claimable-rewards -b 14234904 --format_json
credmark-dev run curve-fi.all-gauge-claim-addresses --input '{"address":"0x824F13f1a2F29cFEEa81154b46C0fc820677A637"}' -b 14234904 --format_json
credmark-dev run curve-fi.all-gauge-claim-addresses --input '{"address":"0x72E158d38dbd50A483501c24f792bDAAA3e7D55C"}' -b 14234904 --format_json
echo ""
echo "Run Finance Examples"
echo ""
credmark-dev run finance.example-var-contract --input '{"asOf": "2022-02-17", "window": "30 days", "interval": 3, "confidences": [0.01,0.05]}' -l finance.example-var-contract,finance.example-historical-price,finance.var-engine-historical -b 14234904 --format_json
credmark-dev run finance.var-engine --input '{"portfolio": {"positions": [{"amount": -0.5, "asset": {"symbol": "WETH"}}, {"amount": 0.5, "asset": {"symbol": "WETH"}}]}, "window": "30 days","intervals": ["1 day"], "confidences": [0.05], "dev_mode":false, "verbose":true}' -l finance.var-engine,finance.var-reference,token.price-ext,finance.get-one,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run finance.var-engine --input '{"portfolio": {"positions": [{"amount":  0.5, "asset": {"symbol": "WETH"}}, {"amount": 0.5, "asset": {"symbol": "WETH"}}]}, "window": "30 days","intervals": ["1 day"], "confidences": [0.05], "dev_mode":false, "verbose":true}' -l finance.var-engine,finance.var-reference,token.price-ext,finance.get-one,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run finance.var-engine --input '{"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "WETH"}}]}, "window": "30 days", "intervals": ["1 day"], "confidences": [0.05], "dev_mode":false, "verbose":true}' -l finance.var-engine,finance.var-reference,token.price-ext,finance.get-one,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run finance.var-engine --input '{"portfolio": {"positions": [{"amount": -1, "asset": {"symbol": "WETH"}}]}, "window": "30 days", "intervals": ["1 day"], "confidences": [0.05], "dev_mode":false, "verbose":true}' -l finance.var-engine,finance.var-reference,token.price-ext,finance.get-one,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run finance.var-engine --input '{"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "WETH"}}]}, "window": "90 days", "intervals": ["1 day","10 days"], "confidences": [0.01,0.05], "dev_mode":false, "verbose":true}' -l finance.var-engine,finance.var-reference,token.price-ext,finance.get-one,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
credmark-dev run finance.var-regtest --input '{}' -l finance.var-engine,finance.var-reference,token.price-ext,finance.get-one,finance.var-engine,finance.var-reference,token.price-ext,finance.get-one,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
