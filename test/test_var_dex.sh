echo "Longer Test for LP VaR"

credmark-dev run finance.var-dex-lp -i '{"pool": {"address":"0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58"},
"window":"280 days", "interval":10, "confidence": 0.01, "lower_range": 0.01, "upper_range":0.01, "price_model":"chainlink.price-usd"}' -b 13909787 -j --api_url=http://localhost:8700

for range_of_pool in 0.01 0.05 0.1 0.2 0.4 0.6 0.8 1.0; do
    echo ${range_of_pool}
    credmark-dev run finance.var-dex-lp -i '{"pool": {"address":"0xcbcdf9626bc03e24f779434178a73a0b4bad62ed"},
    "window":"280 days", "interval":10, "confidence": 0.01, "lower_range": '${range_of_pool}', "upper_range": '${range_of_pool}', "price_model":"chainlink.price-usd"}' -b 13909787 -j --api_url=http://localhost:8700
done
