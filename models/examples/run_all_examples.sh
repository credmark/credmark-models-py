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
echo "Run 30 day Series Example:"
echo ""
credmark-dev run example-30-day-series --input '{"slug":"example-echo", "input":{"message":"hello world"}}' --api_url=http://localhost:8700/v1/models/run -b 14234904
