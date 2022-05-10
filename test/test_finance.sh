echo_cmd ""
echo_cmd "Run Finance Examples"
echo_cmd ""

test_model 0 finance.example-var-contract '{"asOf": "2022-02-17", "window": "30 days", "interval": 3, "confidences": [0.01,0.05]}' finance.example-var-contract,finance.example-historical-price,finance.var-engine-historical
test_model 0 finance.lcr '{"address": "0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0", "cashflow_shock": 1e10}'
test_model 0 finance.min-risk-rate '{}' compound-v2.get-pool-info,compound-v2.all-pools-info
test_model 0 finance.var-aave '{"asOf": "2022-02-17", "window": "30 days", "interval": 3, "confidences": [0.01,0.05]}' finance.example-var-contract,finance.example-historical-price,finance.var-engine-historical
test_model 0 finance.var-compound '{"asOf": "2022-02-17", "window": "30 days", "interval": 3, "confidences": [0.01,0.05]}' finance.example-var-contract,finance.example-historical-price,finance.var-engine-historical
test_model 0 finance.sharpe-ratio-token '{"token": {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}, "window": "10 minute", "risk_free_rate": 0.02}'
test_model 0 finance.sharpe-ratio-token '{"token": {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}, "window": "360 days", "risk_free_rate": 0.02}'
