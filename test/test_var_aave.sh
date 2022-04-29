aave_deps=aave.token-asset,aave.lending-pool-assets

test_model 0 finance.var-aave-plan '{"window": "30 days", "intervals": ["10 day"], "confidences": [0.01], "dev_mode":false, "verbose":true}' ${aave_deps},${var_deps}
test_model 0 finance.var-aave-plan '{"window": "30 days", "intervals": ["10 day"], "as_ofs": ["2022-02-10", "2022-02-15"], "as_of_is_range":true, "confidences": [0.01], "dev_mode":false, "verbose":true}' ${aave_deps},${var_deps}

# only to get history
test_model 0 finance.var-aave-plan '{"window": "1 days", "intervals": ["10 day"], "as_ofs": ["2020-11-30", "2022-02-18"], "as_of_is_range":true, "confidences": [0.01], "dev_mode":true, "verbose":true, "aave_history":true}' ${aave_deps},${var_deps}

rm tmp/aave-[0-9]

test_model 0 finance.var-aave-plan '{"window": "1000 days", "intervals": ["1 day"], "as_ofs": ["2022-02-15"], "as_of_is_range":true, "confidences": [0.01], "dev_mode":true, "verbose":true, "aave_history":false}' ${aave_deps},${var_deps}

# aave var history
test_model 0 finance.var-aave-plan '{"window": "365 days", "intervals": ["10 day"], "as_ofs": ["2020-11-30", "2021-01-15"], "as_of_is_range":true, "confidences": [0.01], "dev_mode":true, "verbose":true, "aave_history":false}' ${aave_deps},${var_deps}
touch tmp/aave-0

test_model 0 finance.var-aave-plan '{"window": "365 days", "intervals": ["10 day"], "as_ofs": ["2021-01-15", "2021-03-01"], "as_of_is_range":true, "confidences": [0.01], "dev_mode":true, "verbose":true, "aave_history":false}' ${aave_deps},${var_deps}
touch tmp/aave-1

test_model 0 finance.var-aave-plan '{"window": "365 days", "intervals": ["10 day"], "as_ofs": ["2021-03-01", "2021-04-15"], "as_of_is_range":true, "confidences": [0.01], "dev_mode":true, "verbose":true, "aave_history":false}' ${aave_deps},${var_deps}
touch tmp/aave-2

test_model 0 finance.var-aave-plan '{"window": "365 days", "intervals": ["10 day"], "as_ofs": ["2021-04-15", "2021-06-01"], "as_of_is_range":true, "confidences": [0.01], "dev_mode":true, "verbose":true, "aave_history":false}' ${aave_deps},${var_deps}
touch tmp/aave-3

test_model 0 finance.var-aave-plan '{"window": "365 days", "intervals": ["10 day"], "as_ofs": ["2021-06-01", "2021-07-15"], "as_of_is_range":true, "confidences": [0.01], "dev_mode":true, "verbose":true, "aave_history":false}' ${aave_deps},${var_deps}
touch tmp/aave-4

test_model 0 finance.var-aave-plan '{"window": "365 days", "intervals": ["10 day"], "as_ofs": ["2021-07-15", "2021-09-30"], "as_of_is_range":true, "confidences": [0.01], "dev_mode":true, "verbose":true, "aave_history":false}' ${aave_deps},${var_deps}
touch tmp/aave-5

test_model 0 finance.var-aave-plan '{"window": "365 days", "intervals": ["10 day"], "as_ofs": ["2021-09-30", "2021-11-15"], "as_of_is_range":true, "confidences": [0.01], "dev_mode":true, "verbose":true, "aave_history":false}' ${aave_deps},${var_deps}
touch tmp/aave-6

test_model 0 finance.var-aave-plan '{"window": "365 days", "intervals": ["10 day"], "as_ofs": ["2021-11-15", "2021-12-31"], "as_of_is_range":true, "confidences": [0.01], "dev_mode":true, "verbose":true, "aave_history":false}' ${aave_deps},${var_deps}
touch tmp/aave-7

test_model 0 finance.var-aave-plan '{"window": "365 days", "intervals": ["10 day"], "as_ofs": ["2021-12-31", "2022-02-15"], "as_of_is_range":true, "confidences": [0.01], "dev_mode":true, "verbose":true, "aave_history":false}' ${aave_deps},${var_deps}
touch tmp/aave-8
