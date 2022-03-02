@echo off

credmark-dev list

echo ""
echo "ECHO Example:"
echo ""
credmark-dev run example-echo --input "{""message"":""hello world""}" -b 14234904 --api_url=http://localhost:8700/v1/models/run
echo ""
echo "BLOCKNUMBER Example:"
echo ""
credmark-dev run example-blocktime --input "{}" -b 14234904 --api_url=http://localhost:8700/v1/models/run
echo ""
echo "Address Examples:"
echo ""
credmark-dev run example-address --input '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}' -b 14234904
credmark-dev run example-address-transforms --input '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}' -b 14234904 --api_url=http://localhost:8700/v1/models/run
echo ""
echo "Load Contract Examples:"
echo ""
credmark-dev run example-load-contract-by-name --input '{"contractName": "mutantmfers"}' -b 14234904 --api_url=http://localhost:8700/v1/models/run
credmark-dev run example-load-contract-by-address --input '{"address": "0xa8f8dd56e2352e726b51738889ef6ee938cca7b6"}' -b 14234904 --api_url=http://localhost:8700/v1/models/run
echo ""
echo "Load Contract By Name Example:"
echo ""
credmark-dev run example-load-contract-by-name --input '{"contractName": "mutantmfers"}' -b 14234904 --api_url=http://localhost:8700/v1/models/run
echo ""
echo "Run 30 day Series Example:"
echo ""
credmark-dev run example-30-day-series --input '{"slug":"example-echo", "input":{"message":"hello world"}}' -b 14234904 --api_url=http://localhost:8700/v1/models/run

credmark-dev run var -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run cmk-total-supply -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run cmk-circulating-supply -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run xcmk-total-supply -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run xcmk-cmk-staked -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run xcmk-deployment-time -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run curve-fi-pool-info -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {"address":"0x06364f10B501e868329afBc005b3492902d6C763"}
credmark-dev run curve-fi-all-pool-info -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run curve-fi-pools -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run uniswap-quoter-price-usd -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run uniswap-router-price-usd -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run uniswap-tokens -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run uniswap-exchange -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run uniswap-v3-get-pools -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run uniswap-v3-get-pool-info -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run uniswap-v3-get-average-price -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run erc20-totalSupply -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run erc20-balanceOf -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run example-address -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {"address":"0xd905e2eaebe188fc92179b6350807d8bd91db0D8"}
credmark-dev run example-address-transforms -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {"address":"0xd905e2eaebe188fc92179b6350807d8bd91db0D8"}
credmark-dev run example-blocktime -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run example-load-contract-by-name -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {"contractName":"mutantmfers"}
credmark-dev run example-load-contract-by-address -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {"address":"0xa8f8dd56e2352e726b51738889ef6ee938cca7b6"}
credmark-dev run type-test-1 -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run type-test-2 -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run example-echo -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run example-30-day-series -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {"slug":"example-echo", "input":{"message":"hello world"}}
credmark-dev run historical-pi -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run historical-staked-xcmk -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
credmark-dev run run-test -b 14234904 --api_url=http://localhost:8700/v1/models/run -i {}
