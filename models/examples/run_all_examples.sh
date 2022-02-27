credmark-dev list

credmark-dev run example-blocktime --input '{}' --api_url=http://localhost:7000/v1/models/run -b 14234904
credmark-dev run example-address --input '{"address": "0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836"}' --api_url=http://localhost:7000/v1/models/run -b 14234904
credmark-dev run example-load-contract-by-name --input '{"contractName": "mutantmfers"}' --api_url=http://localhost:7000/v1/models/run -b 14234904
credmark-dev run example-30-day-series --input '{"slug":"echo", "input":{"message":"hello world"}}' --api_url=http://localhost:7000/v1/models/run -b 14234904