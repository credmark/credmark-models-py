test_model 0 compose.map-block-time-series \
'{"modelSlug":"chainlink.price-usd",
  "modelInput":{"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"},
  "endTimestamp": "1645446694",
  "interval": "86400",
  "count":"3",
  "exclusive": "True"}'

test_model 0 compose.map-blocks \
'{"modelSlug":"chainlink.price-usd",
  "modelInput":{"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"},
  "blockNumbers": [14249443,14219443,14209443]}'

test_model 0 compose.map-inputs \
'{"modelSlug":"chainlink.price-usd",
"modelInputs":[
    {"base": {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}},
    {"base": {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}}]}'


test_model 0 price.quote-historical-multiple '{"inputs":[{"base": {"symbol": "AAVE"}}], "interval": 86400, "count": 20, "exclusive": true}'
