echo_cmd ""
echo_cmd "Run Curve Examples"
echo_cmd ""

test_model 0 curve-fi.pool-info '{"address":"0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"}'
test_model 0 curve-fi.pool-tvl '{"address":"0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"}' ${curve_pool_info_tvl}
test_model 0 curve-fi.all-pools '{}' curve-fi.get-registry,curve-fi.get-provider

test_model 0 curve-fi.all-pools-info '{}' __all__

test_model 0 curve-fi.pool-info '{"address":"0x45f783cce6b7ff23b2ab2d70e416cdb7d6055f51"}'
test_model 0 token.price '{"address":"0x075b1bb99792c9e1041ba13afef80c91a1e70fb3"}'
test_model 0 curve-fi.pool-info '{"address":"0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714"}'

# Curve.fi renBTC/wBTC: 0x93054188d876f558f4a66b2ef1d97d16edf0895b
test_model 0 curve-fi.pool-info '{"address":"0x93054188d876f558f4a66b2ef1d97d16edf0895b"}'

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

# Curve.fi Curve.fi ETH/stETH LP: 0x06325440d014e39736583c165c2963ba99faf14e
test_model 0 curve-fi.pool-info '{"address":"0xDC24316b9AE028F1497c275EB9192a3Ea0f67022"}'

# Curve.fi Factory Plain Pool: cvxCRV (cvxcrv-f)
test_model 0 curve-fi.pool-info '{"address":"0x9D0464996170c6B9e75eED71c68B99dDEDf279e8"}'

# Curve.fi cyDAI/cyUSDC/cyUSDT 0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF
test_model 0 curve-fi.pool-info '{"address":"0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF"}'

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
test_model 0 contrib.curve-get-pegging-ratio '{"address": "0xDC24316b9AE028F1497c275EB9192a3Ea0f67022"}'
test_model 0 contrib.curve-get-pegging-ratio-historical '{"pool": {"address": "0xfd5db7463a3ab53fd211b4af195c5bccc1a03890"}, "date_range": ["2022-01-10","2022-01-15"]}'
test_model 0 contrib.curve-get-depegging-amount '{"pool": {"address": "0xfd5db7463a3ab53fd211b4af195c5bccc1a03890"},"token": {"address": "0xd71ecff9342a5ced620049e616c5035f1db98620"}, "desired_ratio": 0.98485645}'

lp_token_addresses="0xD905e2eaeBe188fc92179b6350807D8bd91Db0D8
0xC25a3A3b969415c80451098fa907EC722572917F
0x3b3ac5386837dc563660fb6a0937dfaa5924333b
0x845838df265dcd2c412a1dc9e959c7d08537f8a2
0xdf5e0e81dff6faf3a7e52ba697820c5e32d806a8
0x9fC689CCaDa600B6DF723D9E47D84d76664a1F23
0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3
0x49849C98ae39Fff122806C06791Fa73784FB3675
0x1AEf73d49Dedc4b1778d0706583995958Dc862e6
0x6D65b498cb23deAba52db31c93Da9BFFb340FB8F
0x4f3E8F405CF5aFC05D68142F3783bDfE13811522
0x97E2768e8E73511cA874545DC5Ff8067eB19B787
0x5B5CFE992AdAC0C9D48E05854B2d91C73a003858
0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490"

for lp_addr in $lp_token_addresses; do
    test_model 0 curve-fi.pool-info '{"address":"'$lp_addr'"}'
done