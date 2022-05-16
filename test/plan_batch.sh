python test/test.py run finance.historical-plan -i '{"model_slug": "finance.min-risk-rate", "model_input": {}, "asOf": "2022-05-13", "window": "1000 days", "interval": "1 day", "input_keys": ["WETH"], "save_file":"tmp/mrr_1000day.csv"}' -b 14783373 -j

python test/test.py run finance.historical-plan -i '{"model_slug": "token.price", "model_input": {"symbol": "WETH"}, "asOf": "2022-05-13", "window": "1000 days", "interval": "1 day", "input_keys": ["WETH"], "save_file":"tmp/weth_1000day.csv"}' -b 14783373 -j

python test/test.py run finance.historical-plan -i '{"model_slug": "token.price", "model_input": {"symbol": "WBTC"}, "asOf": "2022-05-13", "window": "1000 days", "interval": "1 day", "input_keys": ["WBTC"], "save_file":"tmp/wbtc_1000day.csv"}' -b 14783373 -j

