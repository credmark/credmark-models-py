test_model 0 compose.map-block-time-series \
'{"modelSlug":"price.oracle-chainlink",
  "modelInput":{"base": {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}},
  "endTimestamp": "1645446694",
  "interval": "86400",
  "count":"3",
  "exclusive": "True"}'

test_model 0 compose.map-blocks \
'{"modelSlug":"price.oracle-chainlink",
  "modelInput":{"base": {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}},
  "blockNumbers": [14249443,14219443,14209443]}'

test_model 0 compose.map-inputs \
'{"modelSlug":"price.oracle-chainlink",
"modelInputs":[
    {"base": {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}},
    {"base": {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}}]}'
