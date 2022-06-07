echo_cmd ""
echo_cmd "Run Curve Examples"
echo_cmd ""

test_model 0 curve-fi.pool-info '{"address":"0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"}'
test_model 0 curve-fi.pool-tvl '{"address":"0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"}' ${curve_pool_info_tvl}
test_model 0 curve-fi.price '{"address":"0xFEEf77d3f69374f66429C91d732A244f074bdf74"}'
test_model 0 curve-fi.price '{"address":"0x6c3f90f043a72fa612cbac8115ee7e52bde6e490"}'

test_model 0 curve-fi.all-pools '{}' curve-fi.get-registry,curve-fi.get-provider

test_model 0 curve-fi.all-pools-info '{}' __all__

# Curve.fi Factory USD Metapool: Alchemix USD: 0x43b4FdFD4Ff969587185cDB6f0BD875c5Fc83f8c
test_model 0 curve-fi.pool-info '{"address":"0x43b4fdfd4ff969587185cdb6f0bd875c5fc83f8c"}'

# Curve.fi DAI/USDC/USDT 0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7
test_model 0 curve-fi.pool-info '{"address":"0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"}'

# Curve.fi USD-BTC-ETH
test_model 0 curve-fi.pool-info '{"address":"0xD51a44d3FaE010294C616388b506AcdA1bfAAE46"}'

# Curve.fi ETH/rETH 0xF9440930043eb3997fc70e1339dBb11F341de7A8
test_model 0 curve-fi.pool-info '{"address":"0xF9440930043eb3997fc70e1339dBb11F341de7A8"}'

# Curve.fi Curve.fi ETH/rETH (rCRV) LP: 0x53a901d48795C58f485cBB38df08FA96a24669D5
test_model 0 curve-fi.pool-info '{"address":"0x53a901d48795C58f485cBB38df08FA96a24669D5"}'

# Curve.fi oBTC/sbtcCRV Gauge Deposit: 0x11137B10C210b579405c21A07489e28F3c040AB1
test_model 0 curve-fi.gauge-yield '{"address":"0x11137B10C210b579405c21A07489e28F3c040AB1"}' curve-fi.get-gauge-stake-and-claimable-rewards
# Curve.fi tbtc2/sbtcCRV-f Gauge Deposit: 0x29284d30bcb70e86a6c3f84cbc4de0ce16b0f1ca
# curve-fi.get-gauge-stake-and-claimable-rewards
test_model 0 curve-fi.gauge-yield '{"address":"0x29284d30bcb70e86a6c3f84cbc4de0ce16b0f1ca"}' __all__
# 0x824F13f1a2F29cFEEa81154b46C0fc820677A637 is Curve.fi rCRV Gauge Deposit (rCRV-gauge)
test_model 0 curve-fi.all-gauge-claim-addresses '{"address":"0x824F13f1a2F29cFEEa81154b46C0fc820677A637"}'
# 0x72E158d38dbd50A483501c24f792bDAAA3e7D55C is Curve.fi FRAX3CRV-f Gauge Deposit (FRAX3CRV-...)
test_model 0 curve-fi.all-gauge-claim-addresses '{"address":"0x72E158d38dbd50A483501c24f792bDAAA3e7D55C"}'
test_model 0 contrib.curve-get-pegging-ratio '{"address": "0xfd5db7463a3ab53fd211b4af195c5bccc1a03890"}'
test_model 0 contrib.curve-get-pegging-ratio-historical '{"pool": {"address": "0xfd5db7463a3ab53fd211b4af195c5bccc1a03890"}, "date_range": ["2022-01-10","2022-01-15"]}'
test_model 0 contrib.curve-get-depegging-amount '{"pool": {"address": "0xfd5db7463a3ab53fd211b4af195c5bccc1a03890"},"token": {"address": "0xd71ecff9342a5ced620049e616c5035f1db98620"}, "desired_ratio": 0.98485645}'
