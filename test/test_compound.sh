echo_cmd ""
echo_cmd "Run Compound Examples:"
echo_cmd ""

# test_model 0 compound-v2.get-pool-info '{"address":"0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4"}' ${token_price_deps},${compound_deps} -b 13233403
test_model 0 compound-v2.get-pool-info '{"address":"0x95b4ef2869ebd94beb4eee400a99824bf5dc325b"}' ${token_price_deps},compound-v2.get-comptroller

test_model 0 compound-v2.get-comptroller '{}'
test_model 0 compound-v2.get-pools '{}' compound-v2.get-pool-info
test_model 0 compound-v2.all-pools-info '{}' compound-v2.get-pool-info,compound-v2.get-pools,${token_price_deps}
test_model 0 compound-v2.pool-value-historical '{"date_range": ["2021-12-15", "2021-12-18"], "token": {"address":"0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4"}}' ${token_price_deps},compound-v2.get-comptroller,compound-v2.get-pool-info,compound-v2.pool-value,compound-v2.all-pools-values
test_model 0 compound-v2.pool-value-historical '{"date_range": ["2021-09-15", "2021-09-20"], "token": {"address":"0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4"}}' ${token_price_deps},compound-v2.get-comptroller,compound-v2.get-pool-info,compound-v2.pool-value,compound-v2.all-pools-values
test_model 0 compound-v2.pool-value-historical '{"date_range": ["2022-01-15", "2022-01-18"], "token": {"address":"0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4"}}' ${token_price_deps},compound-v2.get-comptroller,compound-v2.get-pool-info,compound-v2.pool-value,compound-v2.all-pools-values
