set +x
if [ $1 == 'test' ]
then
    cmk_dev='python test/test.py'
    echo In test mode, using ${cmk_dev}
else
    cmk_dev='credmark-dev'
    echo Use installed version.
fi

run_cmk_model () {
    model=$1
    input=$2
    ${cmk_dev} run ${model} --input ${input} -b 14234904 --api_url=http://localhost:8700/v1/model/run
}

expected () {
    exit_code=$1
    expected=$2
    if [ $exit_code -ne $expected ]
    then
        echo "Stopped with unexpected exit code: $exit_code != $expected."
        exit
    fi
}

test_cmk_model () {
    expected=$1
    model=$2
    input=$3
    run_cmk_model $model $input
    expected $? $expected
}

${cmk_dev} list

echo ""
echo "Example:"
echo ""
test_cmk_model 0 example.echo '{"message":"hello world"}'

echo ""
echo "BLOCKNUMBER Example:"
echo ""
test_cmk_model 0 example.blocktime '{}'


echo ""
echo "Address Examples:"
echo ""
test_cmk_model 0 example.address-transforms '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}'
test_cmk_model 0 example.address-transforms '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}'


echo ""
echo "Load Contract Examples:"
echo ""
test_cmk_model 0 example.load-contract-by-name '{"contractName": "mutantmfers"}'
test_cmk_model 0 example.load-contract-by-address '{"address": "0xa8f8dd56e2352e726b51738889ef6ee938cca7b6"}'

echo ""
echo "Load Contract By Name Example:"
echo ""
test_cmk_model 0 example.load-contract-by-name '{"contractName": "mutantmfers"}'

echo ""
echo "Run Historical Examples:"
echo ""
test_cmk_model 0 example.historical '{"model_slug":"token.overall-volume","model_input":{"symbol": "USDC"}}'
test_cmk_model 0 example.historical '{"model_slug":"price","model_input":{"symbol": "USDC"}}'
test_cmk_model 0 example.historical-snap '{}'
test_cmk_model 0 example.historical-block '{}'
test_cmk_model 0 example.historical-block-snap '{}'

echo ""
echo "Run Ledger Examples:"
echo ""
test_cmk_model 0 example.ledger-token-transfers '{"address":"0x3812D217bB3A0B43aa16985A616A4e0c6A17C65F"}'
test_cmk_model 0 example.ledger-transactions '{}'
test_cmk_model 0 example.ledger-receipts '{}'
test_cmk_model 0 example.ledger-traces '{}' 
test_cmk_model 0 example.ledger-blocks '{}'
test_cmk_model 0 example.ledger-tokens '{}'
test_cmk_model 0 example.ledger-contracts '{}' 

echo ""
echo "Run Iteration Examples:"
echo ""
test_cmk_model 0 example.iteration '{"symbol":"CMK"}'
test_cmk_model 0 price '{"symbol": "CMK"}'

echo ""
echo "Run Token Examples:"
echo ""
test_cmk_model 0 example.token-loading '{}'

echo ""
echo "Run Library Examples:"
echo ""
test_cmk_model 0 example.libraries '{}'

echo ""
echo "Run Uniswap Examples:"
echo ""
test_cmk_model 0 uniswap-quoter-price-usd '{"tokenAddress":"0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"}'

echo ""
echo "Run Uniswap V3 Examples:"
echo ""
test_cmk_model 0 uniswap-v3-get-pools '{"symbol": "CMK"}'
test_cmk_model 0 uniswap-v3-get-pool-info '{"address": "0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3"}'
test_cmk_model 0 uniswap-v3-get-average-price -i '{"symbol": "CMK"}'
# TODO: USDC price wrong
test_cmk_model 0 uniswap-v3-get-historical-price '{"token": {"symbol": "USDC"}, "window": "10 days"}'
test_cmk_model 0 uniswap-v3-get-historical-price '{"token": {"symbol": "CMK"}, "window": "10 days", "interval":"5 days"}'

echo ""
echo "Run SushiSwap Examples:"
echo ""
test_cmk_model 0 sushiswap-get-pool '{"token0":{"symbol":"USDC"}, "token1":{"symbol":"USDC"}}'
test_cmk_model 0 sushiswap-get-pool-info '{"address":"0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"}'

echo ""
echo "Run Aave V2 Examples:"
echo ""
test_cmk_model 0 aave-token-asset-historical '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}'
test_cmk_model 0 aave-token-asset '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}' # USDC
test_cmk_model 0 aave-token-asset '{"symbol":"USDC"}'
test_cmk_model 0 aave-token-asset '{"symbol":"DAI"}'

test_cmk_model 0 
python test/test.py run aave-token-asset-historical --input {"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"} --api_url=http://localhost:8700/v1/model/run -b 14292598

echo ""
echo "Run Curve Examples"
echo ""
test_cmk_model 0 curve-fi-avg-gauge-yield 

python test/test.py run curve-fi-all-yield --input '{"symbol":"DAI"}' --api_url=http://localhost:8700/v1/model/run -b 14292598
python test/test.py run curve-fi-all-pool-info --input '{"symbol":"DAI"}' --api_url=http://localhost:8700/v1/model/run -b 14292598

