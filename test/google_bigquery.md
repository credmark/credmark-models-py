# 1. accounts_state

```sql
SELECT *
FROM `bigquery-public-data.blockchain_analytics_ethereum_mainnet_us.accounts_state`
where address = '0x9e2a58d257963a276452fff1be94c0eb7e2775cc';
```

```bash
time credmark-dev run ledger.account-native-token-transfers -i '{"accounts": ["0x9e2a58d257963a276452fff1be94c0eb7e2775cc"]}' | tee tmp/native-token-tx.txt
```

```sql
result = context.run_model(‘ledger.account-native-token-transfers’, {"accounts": ["0x9e2a58d257963a276452fff1be94c0eb7e2775cc"]})
df = pd.DataFrame(\_context.run_model(result))
```

0x80aba9cd8b02b227f81d54ddded38290dbb23836
