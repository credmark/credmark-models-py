time curl \
-X 'POST' https://gateway.credmark.com/v1/model/run \
-H 'accept: application/json' \
-H 'Content-Type: application/json' \
-H "Authorization: Bearer $CREDMARK_API_KEY" \
-d '{ "slug": "uniswap-v3.lp", "chainId": 1, "blockNumber": "16362800", "input": {"address": "0x297e12154bde98e96d475fc3a554797f7a6139d0"} }' | jq

time curl -X 'POST' https://gateway.credmark.com/v1/model/run \
-H 'accept: application/json' -H 'Content-Type: application/json' -H "Authorization: Bearer $CREDMARK_API_KEY" \
-d '{ "slug": "uniswap-v3.lp", "chainId": 137, "blockNumber": "latest", "input": {"lp": "0x99fd1378ca799ed6772fe7bcdc9b30b389518962"} }' | jq

time curl -X 'POST' https://gateway.credmark.com/v1/model/run \
-H 'accept: application/json' -H 'Content-Type: application/json' -H "Authorization: Bearer $CREDMARK_API_KEY" \
-d '{ "slug": "price.quote", "chainId": 137, "blockNumber": "latest", "input": {"base": {"address": "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270"}} }' | jq
