echo_cmd ""
echo_cmd "Run Finance Examples"
echo_cmd ""

test_model 0 finance.var-portfolio-historical \
'{"window": "20 days", "interval": 1, "confidences": [0.01],
  "price_model": "chainlink.price-usd",
  "portfolio": {"positions":
  [{"amount": 80394, "asset": {"address": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"}},
   {"amount": 39914, "asset": {"symbol": "BNB"}},
   {"amount": 26281671, "asset": {"symbol": "USDT"}},
   {"amount": 23555590, "asset": {"symbol": "USDC"}},
   {"amount": 1937554, "asset": {"address": "0x85f138bfEE4ef8e540890CFb48F620571d67Eda3"}}
  ]}}'

test_model 0 finance.var-portfolio-historical '{"window": "20 days", "interval": 1, "confidences": [0,0.01,0.05,1], "portfolio": {"positions": [{"amount": "0.5", "asset": {"symbol": "WBTC"}}, {"amount": "0.5", "asset": {"symbol": "WETH"}}]}}'
test_model 0 finance.var-aave '{"window": "30 days", "interval": 3, "confidences": [0.01,0.05]}' finance.var-portfolio-historical
test_model 0 finance.var-compound '{"window": "30 days", "interval": 3, "confidences": [0.01,0.05]}' finance.var-portfolio-historical

test_model 0 finance.example-var-contract '{"window": "30 days", "interval": 3, "confidences": [0.01,0.05]}' finance.example-var-contract,finance.example-historical-price,finance.var-engine-historical
test_model 0 finance.lcr '{"address": "0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0", "cashflow_shock": 1e10}'
test_model 0 finance.min-risk-rate '{}' compound-v2.get-pool-info,compound-v2.all-pools-info

test_model 0 finance.sharpe-ratio-token '{"token": {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}, "prices": {"series": [
{"blockNumber": "10", "blockTimestamp": "10", "sampleTimestamp": "10", "output": {"price": 4.2, "src": ""}},
{"blockNumber": "9", "blockTimestamp": "9", "sampleTimestamp": "9", "output": {"price": 3.2, "src": ""}},
{"blockNumber": "8", "blockTimestamp": "8", "sampleTimestamp": "8", "output": {"price": 6.2, "src": ""}},
{"blockNumber": "7", "blockTimestamp": "7", "sampleTimestamp": "7", "output": {"price": 3.2, "src": ""}},
{"blockNumber": "6", "blockTimestamp": "6", "sampleTimestamp": "6", "output": {"price": 1.2, "src": ""}},
{"blockNumber": "5", "blockTimestamp": "5", "sampleTimestamp": "5", "output": {"price": 8.2, "src": ""}},
{"blockNumber": "4", "blockTimestamp": "4", "sampleTimestamp": "4", "output": {"price": 5.2, "src": ""}},
{"blockNumber": "3", "blockTimestamp": "3", "sampleTimestamp": "3", "output": {"price": 7.2, "src": ""}},
{"blockNumber": "2", "blockTimestamp": "2", "sampleTimestamp": "2", "output": {"price": 3.2, "src": ""}},
{"blockNumber": "1", "blockTimestamp": "1", "sampleTimestamp": "1", "output": {"price": 9.2, "src": ""}}],
"errors": []}, "risk_free_rate": 0.02}'

# test_model 0 finance.sharpe-ratio-token '{"token": {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}, "window": "360 days", "risk_free_rate": 0.02}'
