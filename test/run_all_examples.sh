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
credmark-dev run example.block-time --input '{}' -b 14234904
credmark-dev run example.block-number --input '{}' -b 14234904
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

# HERE

