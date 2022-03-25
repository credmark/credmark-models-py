#!/bin/bash

credmark-dev list
echo ""
echo "Neil's example:"
echo ""
credmark-dev run contrib.neilz --input '{}' -b 14234904
echo ""
echo "echo Examples"
echo ""
credmark-dev run example.echo --input '{"message":"hello world"}' -b 14234904
echo ""
echo "CMK Examples:"
echo ""
credmark-dev run cmk.total-supply --input '{}' -b 14234904
credmark-dev run cmk.circulating-supply --input '{"message":"hello world"}' -b 14234904
credmark-dev run xcmk.cmk-staked --input '{}' -b 14234904
credmark-dev run xcmk.total-supply --input '{}' -b 14234904
credmark-dev run xcmk.deployment-time --input '{}' -b 14234904
echo ""
echo "Account Examples:"
echo ""
credmark-dev run account.portfolio --input '{"address": "0xCE017A1dcE5A15668C4299263019c017154ACE17"}' -b 14234904
echo ""
echo "BLOCKNUMBER Example:"
echo ""
credmark-dev run example.blocktime --input '{}' -b 14234904
credmark-dev run example.blocknumber --input '{}' -b 14234904
echo ""
echo "Address Examples:"
echo ""
credmark-dev run example.address-transforms --input '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}' -b 14234904
credmark-dev run example.address-transforms --input '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}' -b 14234904
echo ""
echo "DTO Examples:"
echo ""
credmark-dev run example.type-test-1 --input '{"positions": [{"amount": "4.2", "token": {"symbol": "USDC"}},{"amount": "4.4", "token": {"symbol": "USDT"}}]}' -b 14234904
credmark-dev run example.type-test-2 --input '{"positions": [{"amount": "4.2", "token": {"symbol": "USDC"}},{"amount": "4.4", "token": {"symbol": "USDT"}}]}' -b 14234904
echo ""
echo "Load Contract Examples:"
echo ""
credmark-dev run example.load-contract-by-name --input '{"contractName": "CIM"}' -b 14234904
credmark-dev run example.load-contract-by-address --input '{"address": "0x4c456a17eb8612231f510c62f02c0b4a1922c7ea"}' -b 14234904
echo ""
echo "Run Historical Examples:"
echo ""
credmark-dev run example.historical --input '{"model_slug":"token.overall-volume","model_input":{"symbol": "USDC"}}' -b 14234904
credmark-dev run example.historical --input '{"model_slug":"token.price","model_input":{"symbol": "USDC"}}' -b 14234904
credmark-dev run example.historical-snap --input '{}' -b 14234904
credmark-dev run example.historical-block --input '{}' -b 14234904
credmark-dev run example.historical-block-snap --input '{}' -b 14234904
echo ""
echo "Run Ledger Examples:"
echo ""
credmark-dev run example.ledger-token-transfers --input '{"address":"0x3812D217bB3A0B43aa16985A616A4e0c6A17C65F"}' -b 14234904
credmark-dev run example.ledger-transactions --input '{}' -b 14234904
credmark-dev run example.ledger-receipts --input '{}' -b 14234904
credmark-dev run example.ledger-traces --input '{}' -b 14234904
credmark-dev run example.ledger-blocks --input '{}' -b 14234904
credmark-dev run example.ledger-tokens --input '{}' -b 14234904
credmark-dev run example.ledger-contracts --input '{}' -b 14234904
credmark-dev run example.ledger-logs --input '{}' -b 14234904
echo ""
echo "Run Iteration Examples:"
echo ""
credmark-dev run example.iteration --input '{}' -b 14234904
echo ""
echo "Run Token Examples:"
echo ""
credmark-dev run example.token-loading --input '{}' -b 14234904
credmark-dev run price --input '{"symbol": "CMK"}' -b 14234904
credmark-dev run token.holders --input '{"symbol": "CMK"}' -b 14234904
credmark-dev run token.swap-pools --input '{"symbol":"CMK"}' -b 14234904
credmark-dev run token.info --input '{"symbol":"CMK"}' -b 14234904
credmark-dev run token.swap-pool-volume --input '{"address":"0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f"}' -b 14234904
credmark-dev run token.categorized-supply --input '{"categories": [{"accounts": {"accounts": [{"address": "0x1F98431c8aD98523631AE4a59f267346ea31F984"}]}, "categoryName": "", "categoryType": "", "circulating": true}], "token": {"symbol": "DAI"}}' -b 14234904
echo ""
echo "Run TestRun Example:"
echo ""
credmark-dev run example.run-test --input '{"model":"price","input":{"symbol": "CMK"}}' -b 14234904
echo ""
echo "Run Library Examples:"
echo ""
credmark-dev run example.libraries --input '{}' -b 14234904
echo ""
echo "Run Compound Examples:"
echo ""
credmark-dev run compound.test --input '{"symbol":"USDC"}' -b 14234904
credmark-dev run compound-token-asset --input '{"symbol":"DAI"}' -b 14234904
credmark-dev run compound-token-liability --input '{"symbol":"DAI"}' -b 14234904
echo ""
echo "Run Uniswap Examples:"
echo ""
credmark-dev run uniswap.tokens --input '{}' -b 14234904
credmark-dev run uniswap.exchange --input '{}' -b 14234904
credmark-dev run uniswap.quoter-price-usd --input '{"tokenAddress":"0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"}' -b 14234904
credmark-dev run uniswap.router-price-usd --input '{}' -b 14234904
echo ""
echo "Run Uniswap V3 Examples:"
echo ""
credmark-dev run uniswap-v3.get-pools --input '{"symbol": "CMK"}' -b 14234904
credmark-dev run uniswap-v3.get-pool-info --input '{"address": "0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3"}' -b 14234904
credmark-dev run uniswap-v3.get-average-price --input '{"symbol": "CMK"}' -b 14234904
credmark-dev run uniswap-v3.get-historical-price --input '{"token": {"symbol": "USDC"}, "window": "10 days"}' -b 14234904
credmark-dev run uniswap-v3.get-historical-price --input '{"token": {"symbol": "CMK"}, "window": "10 days", "interval":"5 days"}' -b 14234904
echo ""
echo "Run SushiSwap Examples:"
echo ""
credmark-dev run sushiswap.all-pools --input '{}' -b 14234904
credmark-dev run sushiswap.get-pool --input '{"token0":{"symbol":"USDC"}, "token1":{"symbol":"USDC"}}' -b 14234904
credmark-dev run sushiswap.get-pool-info --input '{"address":"0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"}' -b 14234904
echo ""
echo "Run Aave V2 Examples:"
echo ""
credmark-dev run aave.lending-pool-assets --input '{}' -b 14234904
credmark-dev run aave.token-liability --input '{"symbol":"USDC"}' -b 14234904
credmark-dev run aave.overall-liabilities-portfolio --input '{}' -b 14234904
credmark-dev run aave.token-asset-historical --input '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}' -b 14234904
credmark-dev run aave.token-asset --input '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}' -b 14234904
credmark-dev run aave.token-asset --input '{"symbol":"USDC"}' -b 14234904
credmark-dev run aave.token-asset --input '{"symbol":"DAI"}' -b 14234904
echo ""
echo "Run Curve Examples"
echo ""
credmark-dev run curve-fi-avg-gauge-yield --input '{"address":"0x72E158d38dbd50A483501c24f792bDAAA3e7D55C"}' -b 14234904
credmark-dev run curve-fi-all-yield --input '{}' -b 14234904
credmark-dev run curve-fi-all-pool-info --input '{}' -b 14234904
credmark-dev run curve-fi-historical-lp-dist --input '{"address":"0x853d955aCEf822Db058eb8505911ED77F175b99e"}' -b 14234904
echo ""
echo "Run Finance Examples"
echo ""
credmark-dev run finance.lcr --input '{"address": "0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0", "cashflow_shock": 1e10}' -b 14234904
credmark-dev run finance.var --input '{"portfolio": {"positions": [{"amount": -0.5, "token": {"symbol": "WETH"}}, {"amount": 0.5, "token": {"symbol": "WETH"}}]}, "window": "30 days","intervals": ["1 day"], "confidences": [0.05], "dev_mode":true}' -b 14234904
credmark-dev run finance.var --input '{"portfolio": {"positions": [{"amount":  0.5, "token": {"symbol": "WETH"}}, {"amount": 0.5, "token": {"symbol": "WETH"}}]}, "window": "30 days","intervals": ["1 day"], "confidences": [0.05], "dev_mode":true}' -b 14234904
credmark-dev run finance.var --input '{"portfolio": {"positions": [{"amount":  1, "token": {"symbol": "WETH"}}]}, "window": "30 days", "intervals": ["1 day"], "confidences": [0.05], "dev_mode":true}' -b 14234904
credmark-dev run finance.var --input '{"portfolio": {"positions": [{"amount": -1, "token": {"symbol": "WETH"}}]}, "window": "30 days", "intervals": ["1 day"], "confidences": [0.05], "dev_mode":true}' -b 14234904
credmark-dev run finance.var --input '{"portfolio": {"positions": [{"amount":  1, "token": {"symbol": "WETH"}}]}, "window": "90 days", "intervals": ["1 day","10 days"], "confidences": [0.01,0.05], "dev_mode":true}' -b 14234904
