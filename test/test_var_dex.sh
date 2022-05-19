credmark-dev run finance.dex-lp-var -i '{"pool": {"address":"0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58"},
"window":"280 days", "interval":10, "confidences": [0.01], "lower_range": 0.01, "upper_range":0.01, "price_model":"chainlink.price-usd"}' -b 13909787

credmark-dev run finance.dex-lp-var -i '{"pool": {"address":"0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58"},
"window":"280 days", "interval":10, "confidences": [0.01], "lower_range": 0.05, "upper_range":0.05, "price_model":"chainlink.price-usd"}' -b 13909787

credmark-dev run finance.dex-lp-var -i '{"pool": {"address":"0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58"},
"window":"280 days", "interval":10, "confidences": [0.01], "lower_range": 0.10, "upper_range":0.10, "price_model":"chainlink.price-usd"}' -b 13909787

credmark-dev run finance.dex-lp-var -i '{"pool": {"address":"0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58"},
"window":"280 days", "interval":10, "confidences": [0.01], "lower_range": 0.40, "upper_range":0.40, "price_model":"chainlink.price-usd"}' -b 13909787

credmark-dev run finance.dex-lp-var -i '{"pool": {"address":"0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58"},
"window":"280 days", "interval":10, "confidences": [0.01], "lower_range": 0.60, "upper_range":0.60, "price_model":"chainlink.price-usd"}' -b 13909787

credmark-dev run finance.dex-lp-var -i '{"pool": {"address":"0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58"},
"window":"280 days", "interval":10, "confidences": [0.01], "lower_range": 0.80, "upper_range":0.80, "price_model":"chainlink.price-usd"}' -b 13909787
