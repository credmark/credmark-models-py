# token.deployment

```bash
credmark-dev run token.deployment -i '{"address":"0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6"}'  -b 42499488 -j -c 137 -l -

credmark-dev run token.deployment -i '{"address":"0xc9c785d61455a44e9281c60d19e97a5fdd858510"}' -c 137 -j -l -

credmark-dev run token.deployment -i '{"address":"0xc9c785d61455a44e9281c60d19e97a5fdd858510"}' -c 137 -j -l - -b 39527975 -l -

# 38521413
```

# contract.events

```bash
credmark-dev run contract.events -i '{"address": "0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6", "event_name": "Deposit", "event_abi": [{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"shares","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Deposit","type":"event"}]}' -c 137 -j -b 42499488 -l -
```

```bash
credmark-dev run contract.events -i '{"address": "0xc9c785d61455a44e9281c60d19e97a5fdd858510", "event_name": "Deposit", "event_abi": [{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"shares","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Deposit","type":"event"}]}' -b 39527975 -j -c 137 -l - --api_url http://localhost:8700
```

# vault-cashflow

```bash
credmark-dev run ichi.vault-cashflow -i '{"address":"0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6"}' -b 42499488 -j -c 137 -l -

credmark-dev run ichi.vault-cashflow -i '{"address":"0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6"}' -b 42499488 -j -c 137 -l '*'
```

```bash
credmark-dev run ichi.vault-cashflow -i '{"address":"0xc9c785d61455a44e9281c60d19e97a5fdd858510"}' -b 39527975 -j -c 137 -l -

credmark-dev run ichi.vault-cashflow -i '{"address":"0xc9c785d61455a44e9281c60d19e97a5fdd858510"}' -b 39527975 -j -c 137 -l - --api_url http://localhost:8700
```

# vault-performance

```bash
credmark-dev run ichi.vault-performance -i '{"address":"0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6"}' --api_url http://localhost:8700 -b 42499488 -j -c 137 -l -

credmark-dev run ichi.vault-performance -i '{"address":"0xc9c785d61455a44e9281c60d19e97a5fdd858510"}' -b 39527975 -j -c 137 -l -
```

# vaults-performance

```bash
credmark-dev run ichi.vaults-performance -i '{}' -b 39527975 -j -c 137 -l -
```

# token.deployment

```bash
credmark-dev --model_path x run token.deployment -j -i '{"address": "0x692437de2cae5addd26ccf6650cad722d914d974", "ignore_proxy": true}' -l - -c 137

"type": "ModelDataError",
    "message": "0x692437de2cae5addd26ccf6650cad722d914d974 is not an EOA account on block 28197291 because it would be deployed on 39530703.",
    "stack": [
        {
            "slug": "token.deployment",

```

```bash
credmark-dev --model_path x run token.deployment -j -i '{"address": "0xe5bf5d33c617556b91558aafb7beadb68e9cea81", "ignore_proxy": true}' -l - -c 137
```
