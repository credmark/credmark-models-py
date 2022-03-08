python test\test.py list

function test-exit-code {
    Param($exit_code, [int]$expected)

    if ($exit_code -ne $expected) {
        Write-Error "[test-this] Stopped with unexpected exit code: $exit_code != $expected."
        exit
    }
}

python test\test.py run erc20-totalSupply --input '{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}' --api_url=http://localhost:8700/v1/model/run -b 14292598

python test\test.py run example.historical --input '{"model_slug":"erc20-totalSupply","model_input":{"address":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}}' --api_url=http://localhost:8700/v1/model/run -b 14292598

echo ""
echo "Run Historical Examples:"
echo ""
python test\test.py run example.historical --input '{}' --api_url=http://localhost:8700/v1/model/run -b 14292598
test-exit-code $LASTEXITCODE 1
python test\test.py run example.historical-snap --input '{}' --api_url=http://localhost:8700/v1/model/run -b 14292598
test-exit-code $LASTEXITCODE 1
python test\test.py run example.historical-block --input '{}' --api_url=http://localhost:8700/v1/model/run -b 14292598
test-exit-code $LASTEXITCODE 1
python test\test.py run example.historical-block-snap --input '{}' --api_url=http://localhost:8700/v1/model/run -b 14292598
test-exit-code $LASTEXITCODE 1


echo ""
echo "Run Ledger Examples:"
echo ""
python test\test.py run example.ledger-logs --input '{}' --api_url=http://localhost:8700/v1/model/run -b 14292599
test-exit-code $LASTEXITCODE 0
python test\test.py run example.ledger-token-transfers --input '{"address":"0x3812D217bB3A0B43aa16985A616A4e0c6A17C65F"}' --api_url=http://localhost:8700/v1/model/run -b 14292599
test-exit-code $LASTEXITCODE 0
python test\test.py run example.ledger-transactions --input '{}' --api_url=http://localhost:8700/v1/model/run -b 14292599
test-exit-code $LASTEXITCODE 0
python test\test.py run example.ledger-receipts --input '{}' --api_url=http://localhost:8700/v1/model/run -b 14292599
test-exit-code $LASTEXITCODE 0
python test\test.py run example.ledger-traces --input '{}'  --api_url=http://localhost:8700/v1/model/run -b 14292599
test-exit-code $LASTEXITCODE 0
python test\test.py run example.ledger-blocks --input '{}' --api_url=http://localhost:8700/v1/model/run -b 14292599
test-exit-code $LASTEXITCODE 0
python test\test.py run example.ledger-tokens --input '{}' --api_url=http://localhost:8700/v1/model/run -b 14292599
test-exit-code $LASTEXITCODE 0
python test\test.py run example.ledger-contracts --input '{}'  --api_url=http://localhost:8700/v1/model/run -b 14292599
test-exit-code $LASTEXITCODE 0

echo ""
echo "Load Contract By Name Example:"
echo ""
python test\test.py run example.load-contract-by-name --input '{"contractName": "mutantmfers"}' --api_url=http://localhost:8700/v1/model/run -b 14234904
test-exit-code $LASTEXITCODE 0

echo ""
echo "Run Iteration Examples:"
echo ""
python test\test.py run example.iteration --input '{"symbol":"CMK"}' --api_url=http://localhost:8700/v1/model/run -b 14282599
test-exit-code $LASTEXITCODE 0

echo ""
echo "Run Token Examples:"
echo ""
python test\test.py run example.token-loading --input '{}' --api_url=http://localhost:8700/v1/model/run -b 14292599
test-exit-code $LASTEXITCODE 0

python test\test.py run example.token-input --input '{"address":"0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}' --api_url=http://localhost:8700/v1/model/run -b 14292599
test-exit-code $LASTEXITCODE 0

echo ""
echo "ECHO Example:"
echo ""
python test\test.py run example.echo --input '{"message":"hello world"}' -b 14234904
test-exit-code $LASTEXITCODE 0

echo ""
echo "BLOCKNUMBER Example:"
echo ""
python test\test.py run example.blocktime --input '{}' --api_url=http://localhost:8700/v1/model/run -b 14234904
test-exit-code $LASTEXITCODE 0

echo ""
echo "Address Examples:"
echo ""
python test\test.py run example.address --input '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}' --api_url=http://localhost:8700/v1/model/run -b 14234904
test-exit-code $LASTEXITCODE 0
python test\test.py run example.address-transforms --input '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}' --api_url=http://localhost:8700/v1/model/run -b 14234904
test-exit-code $LASTEXITCODE 0

echo ""
echo "Load Contract Examples:"
echo ""
python test\test.py run example.load-contract-by-name --input '{"contractName": "mutantmfers"}' --api_url=http://localhost:8700/v1/model/run -b 14234904
test-exit-code $LASTEXITCODE 0
python test\test.py run example.load-contract-by-address --input '{"address": "0xa8f8dd56e2352e726b51738889ef6ee938cca7b6"}' --api_url=http://localhost:8700/v1/model/run -b 14234904
test-exit-code $LASTEXITCODE 0

echo ""
echo "Load Contract By Name Example:"
echo ""
python test\test.py run example.load-contract-by-name --input '{"contractName": "mutantmfers"}' --api_url=http://localhost:8700/v1/model/run -b 14234904
test-exit-code $LASTEXITCODE 0
