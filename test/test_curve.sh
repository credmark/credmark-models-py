echo_cmd ""
echo_cmd "Run Curve Examples"
echo_cmd ""

test_model 0 curve-fi.all-pools '{}' curve-fi.get-registry,curve-fi.get-provider
# Curve.fi Factory USD Metapool: Alchemix USD: 0x43b4FdFD4Ff969587185cDB6f0BD875c5Fc83f8c
test_model 0 curve-fi.pool-info '{"address":"0x43b4fdfd4ff969587185cdb6f0bd875c5fc83f8c"}'
# Running time too long: curve-fi.all-pools-info
# test_model 0 curve-fi.all-yield '{}' curve-fi.all-gauges,curve-fi.pool-info,curve-fi.get-gauge-stake-and-claimable-rewards,curve-fi.gauge-yield
test_model 0 curve-fi.all-gauges '{}' # curve-fi.get-gauge-controller
test_model 0 curve-fi.get-gauge-stake-and-claimable-rewards '{"address":"0x824F13f1a2F29cFEEa81154b46C0fc820677A637"}'
test_model 0 curve-fi.gauge-yield '{"address":"0x824F13f1a2F29cFEEa81154b46C0fc820677A637"}' curve-fi.get-gauge-stake-and-claimable-rewards
# 0x824F13f1a2F29cFEEa81154b46C0fc820677A637 is Curve.fi rCRV Gauge Deposit (rCRV-gauge)
test_model 0 curve-fi.all-gauge-claim-addresses '{"address":"0x824F13f1a2F29cFEEa81154b46C0fc820677A637"}'
# 0x72E158d38dbd50A483501c24f792bDAAA3e7D55C is Curve.fi FRAX3CRV-f Gauge Deposit (FRAX3CRV-...)
test_model 0 curve-fi.all-gauge-claim-addresses '{"address":"0x72E158d38dbd50A483501c24f792bDAAA3e7D55C"}'
test_model 0 contrib.nish-curve-get-pegging-ratio '{"address": "0xfd5db7463a3ab53fd211b4af195c5bccc1a03890"}'
test_model 0 contrib.nish-curve-get-pegging-ratio-historical '{"pool": {"address": "0xfd5db7463a3ab53fd211b4af195c5bccc1a03890"}, "date_range": ["2022-01-10","2022-01-15"]}'
test_model 0 contrib.nish-curve-get-depegging-amount '{"pool": {"address": "0xfd5db7463a3ab53fd211b4af195c5bccc1a03890"},"token": {"address": "0xd71ecff9342a5ced620049e616c5035f1db98620"}, "desired_ratio": 0.98485645}'
