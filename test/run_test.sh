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
test_model 0 example.all '{}'

test_model 0 example.echo '{"message":"hello world"}'
test_model 0 example.contract '{}'

test_model 3 example.data-error '{}'
test_model 3 example.data-error-2 '{}'

test_model 0 example.block-time '{}'
test_model 0 example.block-number '{}'

test_model 0 example.address '{}'

# Fix USDC here
test_model 0 example.type-test-1 '{"positions": [{"amount": "4.2", "asset": {"symbol": "USDC"}},{"amount": "4.4", "asset": {"symbol": "USDT"}}]}'
test_model 1 example.type-test-2 '{"positions": [{"amount": "4.2", "asset": {"symbol": "USDC"}},{"amount": "4.4", "asset": {"symbol": "USDT"}}]}'

test_model 0 example.account '{}'

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


# "address": "0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0"

echo_cmd ""
echo_cmd "Run Historical Examples:"
echo_cmd ""
test_model 0 example.historical '{"model_slug":"token.price-ext","model_input":{"symbol": "USDC"}}'
test_model 0 example.historical '{"model_slug":"token.price","model_input":{"symbol": "USDC"}}'
test_model 0 example.historical '{"model_slug":"token.overall-volume","model_input":{"symbol": "USDC"}}' # series.time-window-interval
test_model 0 example.historical-snap '{}' series.time-start-end-interval
test_model 0 example.historical-block '{}' # series.block-window-intervaluni
test_model 0 example.historical-block-snap '{}' # series.block-start-end-interval

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
test_model 0 token.price '{"symbol": "WETH"}'
test_model 0 token.price '{"symbol": "CMK"}'
test_model 0 token.price '{"symbol": "AAVE"}'
# AAVE: 0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9
test_model 0 token.price '{"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9"}'
test_model 0 token.price '{"symbol": "USDC"}'
test_model 0 token.price '{"symbol": "MKR"}'
# Ampleforth: 0xd46ba6d942050d489dbd938a2c909a5d5039a161
test_model 0 token.price '{"address": "0xd46ba6d942050d489dbd938a2c909a5d5039a161"}'
# RenFil token: 0xD5147bc8e386d91Cc5DBE72099DAC6C9b99276F5
test_model 0 token.price '{"address": "0xD5147bc8e386d91Cc5DBE72099DAC6C9b99276F5"}'

test_model 0 token.price-ext '{"symbol": "CMK"}'

test_model 0 token.holders '{"symbol": "CMK"}'
test_model 0 token.swap-pools '{"symbol":"CMK"}'
test_model 0 token.info '{"symbol":"CMK"}'
test_model 0 token.info '{"address":"0x019Ff0619e1D8Cd2d550940eC743fDE6d268AfE2"}'
test_model 0 token.info '{"address":"0x019ff0619e1d8cd2d550940ec743fde6d268afe2"}'

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
test_model 0 compound.test '{"symbol":"DAI"}'
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
echo_cmd "Run Uniswap V2 Examples:"
echo_cmd ""
test_model 0 uniswap-v2.get-average-price '{"symbol": "USDC"}'
test_model 0 uniswap-v2.get-average-price '{"symbol": "AAVE"}'
test_model 0 uniswap-v2.get-average-price '{"symbol": "DAI"}'
test_model 0 uniswap-v2.get-average-price '{"symbol": "WETH"}'
test_model 0 uniswap-v2.get-average-price '{"symbol": "MKR"}'
# 0xD533a949740bb3306d119CC777fa900bA034cd52: Curve DAO Token (CRV)
test_model 0 uniswap-v2.get-pools '{"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}'
# Uniswap ETH/CRV LP (UNI-V2)
test_model 0 uniswap-v2.pool-volume '{"address": "0x3da1313ae46132a397d90d95b1424a9a7e3e0fce"}'


echo_cmd ""
echo_cmd "Run Uniswap V3 Examples:"
echo_cmd ""
test_model 0 uniswap-v3.get-average-price '{"symbol": "USDC"}'
test_model 0 uniswap-v3.get-average-price '{"symbol": "AAVE"}'
test_model 0 uniswap-v3.get-average-price '{"symbol": "DAI"}'
test_model 0 uniswap-v3.get-average-price '{"symbol": "WETH"}'
test_model 0 uniswap-v3.get-average-price '{"symbol": "MKR"}'
test_model 0 uniswap-v3.get-pools '{"symbol": "MKR"}'
test_model 0 uniswap-v3.get-pool-info '{"address": "0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3"}'
test_model 0 uniswap-v3.get-average-price '{"symbol": "CMK"}'
# TODO: USDC price wrong from USDC/DAI pool
test_model 0 uniswap-v3.get-historical-price '{"token": {"symbol": "USDC"}, "window": "10 days"}'
test_model 0 uniswap-v3.get-historical-price '{"token": {"symbol": "CMK"}, "window": "10 days", "interval":"5 days"}'


echo_cmd ""
echo_cmd "Run SushiSwap Examples:"
echo_cmd ""
test_model 0 sushiswap.get-average-price '{"symbol": "USDC"}'
test_model 0 sushiswap.get-average-price '{"symbol": "AAVE"}'
test_model 0 sushiswap.get-average-price '{"symbol":"DAI"}'
test_model 0 sushiswap.get-average-price '{"symbol":"WETH"}'
test_model 0 sushiswap.get-average-price '{"symbol":"MKR"}'
test_model 0 sushiswap.all-pools '{}'
test_model 0 sushiswap.get-pool '{"token0":{"symbol":"DAI"}, "token1":{"symbol":"WETH"}}'
test_model 0 sushiswap.get-pool-info '{"address":"0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"}'
test_model 0 sushiswap.get-pools '{"address":"0x68CFb82Eacb9f198d508B514d898a403c449533E"}' # CMK_ADDRESS

echo_cmd ""
echo_cmd "Run Aave V2 Examples:"
echo_cmd ""
test_model 0 aave.lending-pool-assets '{}'
# 0xE41d2489571d322189246DaFA5ebDe1F4699F498: ZRX
test_model 0 aave.token-liability '{"address":"0xE41d2489571d322189246DaFA5ebDe1F4699F498"}'
test_model 0 aave.token-liability '{"symbol":"USDC"}'
test_model 0 aave.overall-liabilities-portfolio '{}'
# 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48: USDC
test_model 0 aave.token-asset-historical '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}'
test_model 0 aave.token-asset '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}'
test_model 0 aave.token-asset '{"symbol":"USDC"}'
test_model 0 aave.token-asset '{"symbol":"DAI"}'

echo_cmd ""
echo_cmd "Run Curve Examples"
echo_cmd ""

test_model 0 curve-fi.all-pools '{}'
test_model 0 curve-fi.pool-info '{"address":"0x43b4fdfd4ff969587185cdb6f0bd875c5fc83f8c"}'
test_model 0 curve-fi.pool-historical-reserve '{"address":"0x43b4fdfd4ff969587185cdb6f0bd875c5fc83f8c"}'

test_model 0 curve-fi.all-yield '{}'

test_model 0 curve-fi.all-gauges '{}'
test_model 0 curve-fi.get-gauge-stake-and-claimable-rewards '{"address":"0x824F13f1a2F29cFEEa81154b46C0fc820677A637"}'
test_model 0 curve-fi.gauge-yield '{"address":"0x824F13f1a2F29cFEEa81154b46C0fc820677A637"}'
# 0x824F13f1a2F29cFEEa81154b46C0fc820677A637 is Curve.fi rCRV Gauge Deposit (rCRV-gauge)
test_model 0 curve-fi.all-gauge-claim-addresses '{"address":"0x824F13f1a2F29cFEEa81154b46C0fc820677A637"}'
# 0x72E158d38dbd50A483501c24f792bDAAA3e7D55C is Curve.fi FRAX3CRV-f Gauge Deposit (FRAX3CRV-...)
test_model 0 curve-fi.all-gauge-claim-addresses '{"address":"0x72E158d38dbd50A483501c24f792bDAAA3e7D55C"}'

echo_cmd ""
echo_cmd "Run Finance Examples"
echo_cmd ""

test_model 0 finance.var-engine '{"portfolio": {"positions": [{"amount": -0.5, "asset": {"symbol": "WETH"}}, {"amount": 0.5, "asset": {"symbol": "WETH"}}]}, "window": "30 days","intervals": ["1 day"], "confidences": [0.05], "dev_mode":false, "verbose":true}'
test_model 0 finance.var-engine '{"portfolio": {"positions": [{"amount":  0.5, "asset": {"symbol": "WETH"}}, {"amount": 0.5, "asset": {"symbol": "WETH"}}]}, "window": "30 days","intervals": ["1 day"], "confidences": [0.05], "dev_mode":false, "verbose":true}'
test_model 0 finance.var-engine '{"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "WETH"}}]}, "window": "30 days", "intervals": ["1 day"], "confidences": [0.05], "dev_mode":false, "verbose":true}'
test_model 0 finance.var-engine '{"portfolio": {"positions": [{"amount": -1, "asset": {"symbol": "WETH"}}]}, "window": "30 days", "intervals": ["1 day"], "confidences": [0.05], "dev_mode":false, "verbose":true}'
test_model 0 finance.var-engine '{"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "WETH"}}]}, "window": "90 days", "intervals": ["1 day","10 days"], "confidences": [0.01,0.05], "dev_mode":false, "verbose":true}'

test_model 0 finance.var-regtest '{}'

exit
