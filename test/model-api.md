1. uniswap-v3.lp

```bash
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
```

2. account.portfolio

```bash
time curl -X 'POST' https://gateway.credmark.com/v1/model/run -H 'accept: application/json' -H 'Content-Type: application/json' -H "Authorization: Bearer $CREDMARK_API_KEY" -d '{ "slug": "account.portfolio", "chainId": 1, "blockNumber": "latest", "input": {"address": "0xa084b6e852976bf162cba174c923f8d373ef4820"} }' | jq

time curl -X 'POST' https://gateway.credmark.com/v1/model/run -H 'accept: application/json' -H 'Content-Type: application/json' -H "Authorization: Bearer $CREDMARK_API_KEY" -d '{ "slug": "account.portfolio", "chainId": 1, "blockNumber": "latest", "input": {"address": "0xa084b6e852976bf162cba174c923f8d373ef4820", "with_price": true}}' | jq

time curl -X 'POST' https://gateway.credmark.com/v1/model/run -H 'accept: application/json' -H 'Content-Type: application/json' -H "Authorization: Bearer $CREDMARK_API_KEY" -d '{ "slug": "accounts.portfolio", "chainId": 1, "blockNumber": "latest", "input": {"accounts": [{"address":"0xa084b6e852976bf162cba174c923f8d373ef4820"}]}}' | jq
```

test on localhost

```bash
credmark-dev run account.portfolio --api_url http://localhost:8700 -i '{"address": "0xa084b6e852976bf162cba174c923f8d373ef4820"}' -j

credmark-dev run account.portfolio --api_url http://localhost:8700 -i '{"address": "0xa084b6e852976bf162cba174c923f8d373ef4820", "with_price": true}' -j

time curl -X 'POST' http://localhost:8700/v1/model/run -H 'accept: application/json' -H 'Content-Type: application/json' -H "Authorization: Bearer $CREDMARK_API_KEY" -d '{ "slug": "price.quote", "chainId": 1, "blockNumber": "latest", "input": {"base": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"}}' | jq

time curl -X 'POST' http://localhost:8700/v1/model/run -H 'accept: application/json' -H 'Content-Type: application/json' -H "Authorization: Bearer $CREDMARK_API_KEY" -d '{ "slug": "account.portfolio", "chainId": 1, "blockNumber": "latest", "input": {"address": "0xa084b6e852976bf162cba174c923f8d373ef4820", "with_price": true}}' | jq
```