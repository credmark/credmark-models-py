time credmark-dev --model_path xxxx run uniswap-v2.get-pool-info -i '{"address":"0x6a091a3406E0073C3CD6340122143009aDac0EDa"}' -b 14823357 -j --api_url=http://localhost:8700
# 39s

Remove some recursive call to price WETH
# 33s

time credmark-dev --model_path xxxx run uniswap-v2.get-pool-info -i '{"address":"0x6a091a3406E0073C3CD6340122143009aDac0EDa"}' -b 14823357 -j --api_url=http://localhost:8700

time credmark-dev --model_path xxxx run uniswap-v2.get-pool-info-token-price -i '{"address":"0x6a091a3406E0073C3CD6340122143009aDac0EDa"}' -b 14823357 -j --api_url=http://localhost:8700

time credmark-dev --model_path xxxx run uniswap-v3.get-pool-info-token-price -i '{"symbol":"CMK"}' -b 14823364 -j --api_url=http://localhost:8700

time credmark-dev --model_path xxxx run price.dex-blended -i '{"symbol":"CMK"}' -b 14823364 -j --api_url=http://localhost:8700
