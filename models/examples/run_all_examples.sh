if [ $# -ge 1 ] && [ $1 == 'test' ]
then
    cmk_dev='python test/test.py'
    echo In test mode, using ${cmk_dev}
else
    cmk_dev='credmark-dev'
    echo Use installed version.
fi

set +x

run_model () {
    model=$1
    input=$2
    if [ $# -eq 3 ] && [ $3 == 'print-command' ]
    then
        echo "${cmk_dev} run ${model} --input '${input}' -b 14234904 --api_url=http://localhost:8700/v1/model/run"
    else
        ${cmk_dev} run ${model} --input "${input}" -b 14234904 --api_url=http://localhost:8700/v1/model/run
    fi
}

test_model () {
    expected=$1
    model=$2
    input=$3
    run_model $model "$input"
    exit_code=$?

    cmd="$(run_model $model "$input" print-command)"    
    if [ $exit_code -ne $expected ]
    then
        echo Failed test with $cmd
        echo "Stopped with unexpected exit code: $exit_code != $expected."
        exit
    else
        echo Passed test with $cmd
    fi
}

${cmk_dev} list | awk -v test_script=$0 '{
    print $0
    if ($0 ~ / - /) {
        m=substr($2, 0, length($2)-1)
        res=""
        ( ("grep " m " "test_script) | getline res )
        if (res == "") {
            print "(Test check) No test for " m
        }
    }
}'

echo ""
echo "Neil's example:"
echo ""
test_model 0 contrib.neilz '{}'

echo ""
echo "Echo Examples"
echo ""
test_model 0 example.echo '{"message":"hello world"}'

echo ""
echo "CMK Examples:"
echo ""
test_model 0 cmk.total-supply '{}'
test_model 0 cmk.total-supply '{}'
test_model 0 cmk.circulating-supply '{"message":"hello world"}'
test_model 0 xcmk.cmk-staked '{}'
test_model 0 xcmk.total-supply '{}'
test_model 0 xcmk.deployment-time '{}'

echo ""
echo "Account Examples:"
echo ""
test_model 0 account.portfolio '{"address": "0xCE017A1dcE5A15668C4299263019c017154ACE17"}'

echo ""
echo "BLOCKNUMBER Example:"
echo ""
test_model 0 example.blocktime '{}'


echo ""
echo "Address Examples:"
echo ""
test_model 0 example.address-transforms '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}'
test_model 0 example.address-transforms '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}'

echo ""
echo "DTO Examples:"
echo ""
test_model 0 example.type-test-1 '{"positions": [{"amount": "4.2", "token": {"symbol": "USDC"}},{"amount": "4.4", "token": {"symbol": "USDT"}}]}
'
test_model 1 example.type-test-2 '{"positions": [{"amount": "4.2", "token": {"symbol": "USDC"}},{"amount": "4.4", "token": {"symbol": "USDT"}}]}
'

echo ""
echo "Load Contract Examples:"
echo ""
test_model 0 example.load-contract-by-name '{"contractName": "mutantmfers"}'
test_model 0 example.load-contract-by-address '{"address": "0xa8f8dd56e2352e726b51738889ef6ee938cca7b6"}'

echo ""
echo "Load Contract By Name Example:"
echo ""
test_model 0 example.load-contract-by-name '{"contractName": "mutantmfers"}'

echo ""
echo "Run Historical Examples:"
echo ""
test_model 0 example.historical '{"model_slug":"token.overall-volume","model_input":{"symbol": "USDC"}}'
test_model 0 example.historical '{"model_slug":"price","model_input":{"symbol": "USDC"}}'
test_model 0 example.historical-snap '{}'
test_model 0 example.historical-block '{}'
test_model 0 example.historical-block-snap '{}'

echo ""
echo "Run Ledger Examples:"
echo ""
test_model 0 example.ledger-token-transfers '{"address":"0x3812D217bB3A0B43aa16985A616A4e0c6A17C65F"}'
test_model 0 example.ledger-transactions '{}'
test_model 0 example.ledger-receipts '{}'
test_model 0 example.ledger-traces '{}' 
test_model 0 example.ledger-blocks '{}'
test_model 0 example.ledger-tokens '{}'
test_model 0 example.ledger-contracts '{}' 
test_model 0 example.ledger-logs '{}' 

echo ""
echo "Run Iteration Examples:"
echo ""
test_model 0 example.iteration '{}'

echo ""
echo "Run Token Examples:"
echo ""
test_model 0 example.token-loading '{}'
test_model 0 price '{"symbol": "CMK"}'
test_model 0 token.holders '{"symbol": "CMK"}'
test_model 0 token.swap-pools '{"symbol":"CMK"}'
test_model 0 token.info '{"symbol":"CMK"}'
# WETH-DAI pool: https://analytics.sushi.com/pairs/0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f
test_model 0 token.swap-pool-volume '{"address":"0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f"}'
# 0xbdfa4f4492dd7b7cf211209c4791af8d52bf5c50
# UniSwap V3 factory: 0x1F98431c8aD98523631AE4a59f267346ea31F984
test_model 0 token.categorized-supply '{"categories": [{"accounts": {"accounts": [{"address": "0x1F98431c8aD98523631AE4a59f267346ea31F984"}]}, "categoryName": "", "categoryType": "", "circulating": true}], "token": {"symbol": "USDC"}}'


echo ""
echo "Run TestRun Example:"
echo ""
test_model example.run-test '{"model":"price","input":{"symbol": "CMK"}}'

echo ""
echo "Run Library Examples:"
echo ""
test_model 0 example.libraries '{}'

echo ""
echo "Run Compound Examples:"
echo ""
test_model 0 compound.test '{"symbol":"DAI"}'
# TODO: fix the model
test_model 1 compound-token-asset '{"symbol":"DAI"}'
# TODO: fix the model
test_model 1 compound-token-liability '{"symbol":"DAI"}'


echo ""
echo "Run Uniswap Examples:"
echo ""
test_model 0 uniswap.tokens '{}'
test_model 0 uniswap.exchange '{}'
test_model 0 uniswap.quoter-price-usd '{"tokenAddress":"0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"}'
test_model 0 uniswap.router-price-usd '{}'


echo ""
echo "Run Uniswap V3 Examples:"
echo ""
test_model 0 uniswap.v3-get-pools '{"symbol": "CMK"}'
test_model 0 uniswap.v3-get-pool-info '{"address": "0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3"}'
test_model 0 uniswap.v3-get-average-price '{"symbol": "CMK"}'
# TODO: USDC price wrong?
test_model 0 uniswap.v3-get-historical-price '{"token": {"symbol": "USDC"}, "window": "10 days"}'
test_model 0 uniswap.v3-get-historical-price '{"token": {"symbol": "CMK"}, "window": "10 days", "interval":"5 days"}'

echo ""
echo "Run SushiSwap Examples:"
echo ""
test_model 0 sushiswap.all-pools '{}'
test_model 0 sushiswap.get-pool '{"token0":{"symbol":"USDC"}, "token1":{"symbol":"USDC"}}'
test_model 0 sushiswap.get-pool-info '{"address":"0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"}'

echo ""
echo "Run Aave V2 Examples:"
echo ""
test_model 0 aave.lending-pool-assets '{}'
test_model 0 aave.token-liability '{"symbol":"USDC"}'
test_model 0 aave.overall-liabilities-portfolio '{}'
test_model 0 aave.token-asset-historical '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}'
test_model 0 aave.token-asset '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}' # USDC
test_model 0 aave.token-asset '{"symbol":"USDC"}'
test_model 0 aave.token-asset '{"symbol":"DAI"}'

echo ""
echo "Run Curve Examples"
echo ""
test_model 0 curve-fi-avg-gauge-yield '{"address":"0x72E158d38dbd50A483501c24f792bDAAA3e7D55C"}' # includes curve-fi-all-gauge-addresses, curve-fi-get-gauge-stake-and-claimable-rewards
test_model 0 curve-fi-all-yield '{}'
test_model 0 curve-fi-all-pool-info '{}' # includes curve-fi-pools, curve-fi-pool-info, curve-fi-pool-historical-reserve
# TODO: model is not finished.
test_model 0 curve-fi-historical-lp-dist '{"address":"0x853d955aCEf822Db058eb8505911ED77F175b99e"}'


echo ""
echo "Run Finance Examples"
echo ""
test_model 0 finance.lcr '{"address": "0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0", "cashflow_shock": 1e10}'

test_model 0 finance.lcr '{"address": "0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0", "cashflow_shock": 1e10}'
