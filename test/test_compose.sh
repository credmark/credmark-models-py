test_model 0 models.compose.map_block_time_series '{"modelSlug":"chainlink.price-usd", "modelInputs":{"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}, "endTimestamp": "1654838819", "interval": "7200", "count":"3", "exclusive": True}'

test_model 0 models.compose.map_blocks '{"modelSlug":"chainlink.price-usd", "modelInput":{"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}, "blockNumbers": [14924970,14930880,14936726]}'

test_model 0 compose.map-inputs '{"modelSlug":"chainlink.price-usd", "modelInputs":[{"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}, {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}]}'
