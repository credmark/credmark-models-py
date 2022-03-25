#!/bin/bash

if [ "`which realpath`" == '' ]
then
   FULL_PATH_TO_SCRIPT="${BASH_SOURCE[0]}"
else
   FULL_PATH_TO_SCRIPT="$(realpath "${BASH_SOURCE[-1]}")"
fi

SCRIPT_DIRECTORY="$(dirname "$FULL_PATH_TO_SCRIPT")"

source $SCRIPT_DIRECTORY/test_common.sh

${cmk_dev} list | awk -v test_script=$0 '{
    print $0
    if ($0 ~ / - /) {
        m=substr($2, 0, length($2)-1)
        res=""
        command = ("grep " m " "test_script)
        ( command | getline res )
        if (res == "") {
            print "(Test check) No test for " m
        }
        close(command)
    }
}'

if [ $gen_cmd -eq 1 ]; then
    echo "${cmk_dev} list" >> $cmd_file
fi

echo_cmd ""
echo_cmd "Neil's example:"
echo_cmd ""
test_model 0 contrib.neilz '{}'

echo_cmd ""
echo_cmd "echo Examples"
echo_cmd ""
test_model 0 example.echo '{"message":"hello world"}'

echo_cmd ""
echo_cmd "CMK Examples:"
echo_cmd ""
test_model 0 cmk.total-supply '{}'
test_model 0 cmk.circulating-supply '{"message":"hello world"}'
test_model 0 xcmk.cmk-staked '{}'
test_model 0 xcmk.total-supply '{}'
test_model 0 xcmk.deployment-time '{}'

echo_cmd ""
echo_cmd "Account Examples:"
echo_cmd ""
test_model 0 account.portfolio '{"address": "0xCE017A1dcE5A15668C4299263019c017154ACE17"}'
# Working but taking long time.
# test_model 0 account.portfolio '{"address": "0xbdfa4f4492dd7b7cf211209c4791af8d52bf5c50"}'

echo_cmd ""
echo_cmd "BLOCKNUMBER Example:"
echo_cmd ""
test_model 0 example.blocktime '{}'
test_model 0 example.blocknumber '{}'


echo_cmd ""
echo_cmd "Address Examples:"
echo_cmd ""
test_model 0 example.address-transforms '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}'
test_model 0 example.address-transforms '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}'

echo_cmd ""
echo_cmd "DTO Examples:"
echo_cmd ""
# Fix USDC here
test_model 0 example.type-test-1 '{"positions": [{"amount": "4.2", "token": {"symbol": "USDC"}},{"amount": "4.4", "token": {"symbol": "USDT"}}]}'
test_model 1 example.type-test-2 '{"positions": [{"amount": "4.2", "token": {"symbol": "USDC"}},{"amount": "4.4", "token": {"symbol": "USDT"}}]}'

echo_cmd ""
echo_cmd "Load Contract Examples:"
echo_cmd ""

test_model 0 example.load-contract-by-name '{"contractName": "CIM"}' # CRISP
test_model 0 example.load-contract-by-address '{"address": "0x4c456a17eb8612231f510c62f02c0b4a1922c7ea"}'

echo_cmd ""
echo_cmd "Run Historical Examples:"
echo_cmd ""
test_model 0 example.historical '{"model_slug":"token.overall-volume","model_input":{"symbol": "USDC"}}'
test_model 0 example.historical '{"model_slug":"token.price","model_input":{"symbol": "USDC"}}'
test_model 0 example.historical-snap '{}'
test_model 0 example.historical-block '{}'
test_model 0 example.historical-block-snap '{}'

echo_cmd ""
echo_cmd "Run Ledger Examples:"
echo_cmd ""
test_model 0 example.ledger-token-transfers '{"address":"0x3812D217bB3A0B43aa16985A616A4e0c6A17C65F"}'
test_model 0 example.ledger-transactions '{}'
test_model 0 example.ledger-receipts '{}'
test_model 0 example.ledger-traces '{}'
test_model 0 example.ledger-blocks '{}'
test_model 0 example.ledger-tokens '{}'
test_model 0 example.ledger-contracts '{}'
test_model 0 example.ledger-logs '{}'

echo_cmd ""
echo_cmd "Run Iteration Examples:"
echo_cmd ""
test_model 0 example.iteration '{}'

echo_cmd ""
echo_cmd "Run Token Examples:"
echo_cmd ""
test_model 0 example.token-loading '{}'
test_model 0 price '{"symbol": "CMK"}'
test_model 0 token.holders '{"symbol": "CMK"}'
test_model 0 token.swap-pools '{"symbol":"CMK"}'
test_model 0 token.info '{"symbol":"CMK"}'
# WETH-DAI pool: https://analytics.sushi.com/pairs/0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f
test_model 0 token.swap-pool-volume '{"address":"0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f"}'
# One account: 0xbdfa4f4492dd7b7cf211209c4791af8d52bf5c50
# UniSwap V3 factory: 0x1F98431c8aD98523631AE4a59f267346ea31F984
test_model 0 token.categorized-supply '{"categories": [{"accounts": {"accounts": [{"address": "0x1F98431c8aD98523631AE4a59f267346ea31F984"}]}, "categoryName": "", "categoryType": "", "circulating": true}], "token": {"symbol": "DAI"}}'


echo_cmd ""
echo_cmd "Run TestRun Example:"
echo_cmd ""
test_model 0 example.run-test '{"model":"price","input":{"symbol": "CMK"}}'

echo_cmd ""
echo_cmd "Run Library Examples:"
echo_cmd ""
test_model 0 example.libraries '{}'

echo_cmd ""
echo_cmd "Run Compound Examples:"
echo_cmd ""
test_model 0 compound.test '{"symbol":"USDC"}'
# TODO: fix the model
test_model 1 compound-token-asset '{"symbol":"DAI"}'
# TODO: fix the model
test_model 1 compound-token-liability '{"symbol":"DAI"}'


echo_cmd ""
echo_cmd "Run Uniswap Examples:"
echo_cmd ""
test_model 0 uniswap.tokens '{}'
test_model 0 uniswap.exchange '{}'
test_model 0 uniswap.quoter-price-usd '{"tokenAddress":"0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"}'
test_model 0 uniswap.router-price-usd '{}'


echo_cmd ""
echo_cmd "Run Uniswap V3 Examples:"
echo_cmd ""
test_model 0 uniswap-v3.get-pools '{"symbol": "CMK"}'
test_model 0 uniswap-v3.get-pool-info '{"address": "0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3"}'
test_model 0 uniswap-v3.get-average-price '{"symbol": "CMK"}'
# TODO: USDC price wrong from USDC/DAI pool
test_model 0 uniswap-v3.get-historical-price '{"token": {"symbol": "USDC"}, "window": "10 days"}'
test_model 0 uniswap-v3.get-historical-price '{"token": {"symbol": "CMK"}, "window": "10 days", "interval":"5 days"}'

echo_cmd ""
echo_cmd "Run SushiSwap Examples:"
echo_cmd ""
test_model 0 sushiswap.all-pools '{}'
test_model 0 sushiswap.get-pool '{"token0":{"symbol":"USDC"}, "token1":{"symbol":"USDC"}}'
test_model 0 sushiswap.get-pool-info '{"address":"0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"}'

echo_cmd ""
echo_cmd "Run Aave V2 Examples:"
echo_cmd ""
test_model 0 aave.lending-pool-assets '{}'
test_model 0 aave.token-liability '{"symbol":"USDC"}'
test_model 0 aave.overall-liabilities-portfolio '{}'
test_model 0 aave.token-asset-historical '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}'
test_model 0 aave.token-asset '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}' # USDC
test_model 0 aave.token-asset '{"symbol":"USDC"}'
test_model 0 aave.token-asset '{"symbol":"DAI"}'

echo_cmd ""
echo_cmd "Run Curve Examples"
echo_cmd ""
test_model 0 curve-fi-avg-gauge-yield '{"address":"0x72E158d38dbd50A483501c24f792bDAAA3e7D55C"}' # includes curve-fi-all-gauge-addresses, curve-fi-get-gauge-stake-and-claimable-rewards
test_model 0 curve-fi-all-yield '{}'
test_model 0 curve-fi-all-pool-info '{}' # includes curve-fi-pools, curve-fi-pool-info, curve-fi-pool-historical-reserve
# TODO: model is not finished.
test_model 0 curve-fi-historical-lp-dist '{"address":"0x853d955aCEf822Db058eb8505911ED77F175b99e"}'

echo_cmd ""
echo_cmd "Run Finance Examples"
echo_cmd ""
test_model 0 finance.lcr '{"address": "0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0", "cashflow_shock": 1e10}'
test_model 0 finance.var '{"portfolio": {"positions": [{"amount": -0.5, "token": {"symbol": "WETH"}}, {"amount": 0.5, "token": {"symbol": "WETH"}}]}, "window": "30 days","intervals": ["1 day"], "confidences": [0.05], "dev_mode":true}'
test_model 0 finance.var '{"portfolio": {"positions": [{"amount":  0.5, "token": {"symbol": "WETH"}}, {"amount": 0.5, "token": {"symbol": "WETH"}}]}, "window": "30 days","intervals": ["1 day"], "confidences": [0.05], "dev_mode":true}'
test_model 0 finance.var '{"portfolio": {"positions": [{"amount":  1, "token": {"symbol": "WETH"}}]}, "window": "30 days", "intervals": ["1 day"], "confidences": [0.05], "dev_mode":true}'
test_model 0 finance.var '{"portfolio": {"positions": [{"amount": -1, "token": {"symbol": "WETH"}}]}, "window": "30 days", "intervals": ["1 day"], "confidences": [0.05], "dev_mode":true}'
test_model 0 finance.var '{"portfolio": {"positions": [{"amount":  1, "token": {"symbol": "WETH"}}]}, "window": "90 days", "intervals": ["1 day","10 days"], "confidences": [0.01,0.05], "dev_mode":true}'
