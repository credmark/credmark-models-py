# token.deployment

```bash
credmark-dev run token.deployment -i '{"address":"0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6"}'  -b 42499488 -j -c 137 -l -
```

credmark-dev run token.deployment -i '{"address":"0xc9c785d61455a44e9281c60d19e97a5fdd858510"}' -c 137 -j -l -

credmark-dev run token.deployment -i '{"address":"0xc9c785d61455a44e9281c60d19e97a5fdd858510"}' -c 137 -j -l - -b 39527975 -l -


# contract.events

```bash
credmark-dev run contract.events -i '{"address": "0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6", "event_name": "Deposit", "event_abi": [{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"shares","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Deposit","type":"event"}]}' -c 137 -j -b 42499488 -l -
```

# vault-cashflow

```bash
credmark-dev run ichi.vault-cashflow -i '{"address":"0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6"}' -b 42499488 -j -c 137 -l -

credmark-dev run ichi.vault-cashflow -i '{"address":"0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6"}' -b 42499488 -j -c 137 -l '*'
```

# vault-performance

```bash
credmark-dev run ichi.vault-performance -i '{"address":"0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6"}' --api_url http://localhost:8700 -b 42499488 -j -c 137 -l -
```