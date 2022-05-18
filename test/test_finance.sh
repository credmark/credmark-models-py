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
test_model 0 finance.sharpe-ratio-token '{"token": {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}, "window": "10 minute", "risk_free_rate": 0.02}'
test_model 0 finance.sharpe-ratio-token '{"token": {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}, "window": "360 days", "risk_free_rate": 0.02}'
