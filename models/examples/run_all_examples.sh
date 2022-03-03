credmark-dev list

echo ""
echo "ECHO Example:"
echo ""
credmark-dev run example-echo --input '{"message":"hello world"}' -b 14234904
echo ""
echo "BLOCKNUMBER Example:"
echo ""
credmark-dev run example-blocktime --input '{}' --api_url=http://localhost:8700/v1/models/run -b 14234904
echo ""
echo "Address Examples:"
echo ""
credmark-dev run example-address --input '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}' --api_url=http://localhost:8700/v1/models/run -b 14234904
credmark-dev run example-address-transforms --input '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}' --api_url=http://localhost:8700/v1/models/run -b 14234904
echo ""
echo "Load Contract Examples:"
echo ""
credmark-dev run example-load-contract-by-name --input '{"contractName": "mutantmfers"}' --api_url=http://localhost:8700/v1/models/run -b 14234904
credmark-dev run example-load-contract-by-address --input '{"address": "0xa8f8dd56e2352e726b51738889ef6ee938cca7b6"}' --api_url=http://localhost:8700/v1/models/run -b 14234904
echo ""
echo "Load Contract By Name Example:"
echo ""
credmark-dev run example-load-contract-by-name --input '{"contractName": "mutantmfers"}' --api_url=http://localhost:8700/v1/models/run -b 14234904
echo ""
echo "Run Historical Examples:"
echo ""
credmark-dev run example-historical --input '{}' --api_url=http://localhost:8700/v1/models/run -b 14292598
credmark-dev run example-historical-snap --input '{}' --api_url=http://localhost:8700/v1/models/run -b 14292598
credmark-dev run example-historical-block --input '{}' --api_url=http://localhost:8700/v1/models/run -b 14292598
credmark-dev run example-historical-block-snap --input '{}' --api_url=http://localhost:8700/v1/models/run -b 14292598
echo ""
echo "Run Ledger Examples:"
echo ""
credmark-dev run example-ledger-logs --api_url=http://localhost:8700/v1/models/run -b 14292599 
credmark-dev run example-ledger-token-transactions --input '{"address":"0x3812D217bB3A0B43aa16985A616A4e0c6A17C65F"}' --api_url=http://localhost:8700/v1/models/run -b 14292599 
credmark-dev run example-ledger-transaction  --api_url=http://localhost:8700/v1/models/run -b 14292599 
credmark-dev run example-ledger-receipts  --api_url=http://localhost:8700/v1/models/run -b 14292599 
credmark-dev run example-ledger-traces  --api_url=http://localhost:8700/v1/models/run -b 14292599 
credmark-dev run example-ledger-blocks  --api_url=http://localhost:8700/v1/models/run -b 14292599 
credmark-dev run example-ledger-tokens --api_url=http://localhost:8700/v1/models/run -b 14292599 
credmark-dev run example-ledger-contracts  --api_url=http://localhost:8700/v1/models/run -b 14292599 
