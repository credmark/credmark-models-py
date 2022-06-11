test_model 0 compose.map-block-time-series '{"modelSlug":"chainlink.price-usd", "modelInput":{"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}, "endTimestamp": "1645446694", "interval": "7200", "count":"3", "exclusive": "True"}'

test_model 0 compose.map-blocks '{"modelSlug":"chainlink.price-usd", "modelInput":{"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}, "blockNumbers": [14249443,14219443,14209443]}'

test_model 0 compose.map-inputs '{"modelSlug":"chainlink.price-usd", "modelInputs":[{"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}, {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}]}'
