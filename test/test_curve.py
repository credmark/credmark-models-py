# pylint:disable=locally-disabled,line-too-long

from cmk_test import CMKTest


class TestCurve(CMKTest):
    def test_poolinfo(self):
        self.title('Curve - Pool Info')

        self.run_model('curve-fi.all-pools', {})  # curve-fi.get-registry,curve-fi.get-provider

        self.run_model('curve-fi.all-pools-info', {})  # __all__

        self.run_model('token.price', {"address": "0x6c3f90f043a72fa612cbac8115ee7e52bde6e490"})
        self.run_model('token.price', {"address": "0x075b1bb99792c9e1041ba13afef80c91a1e70fb3"})
        self.run_model('token.price', {"address": "0xc4ad29ba4b3c580e6d59105fff484999997675ff"})

        # Curve.fi LINK/sLINK
        self.run_model('curve-fi.pool-info',
                       {"address": "0xF178C0b5Bb7e7aBF4e12A4838C7b7c5bA2C623c0"}, block_number=14831356)

        # Curve.fi 4pool USDC/USDT/UST/FRAX (4CRV) 0x4e0915C88bC70750D68C481540F081fEFaF22273
        self.run_model('curve-fi.pool-info',
                       {"address": "0x4e0915C88bC70750D68C481540F081fEFaF22273"}, block_number=14831356)

        # Curve.fi 4pool DAI/USDC/USDT/sUSD 0xA5407eAE9Ba41422680e2e00537571bcC53efBfD
        self.run_model('curve-fi.pool-info',
                       {"address": "0xA5407eAE9Ba41422680e2e00537571bcC53efBfD"}, block_number=14831356)

        # Token: Curve.fi 4pool DAI/USDC/USDT/sUSD 0xc25a3a3b969415c80451098fa907ec722572917f
        self.run_model('curve-fi.pool-info', {"address": "0xc25a3a3b969415c80451098fa907ec722572917f"})

        # Curve.fi USD-BTC-ETH 0xc4ad29ba4b3c580e6d59105fff484999997675ff
        self.run_model('curve-fi.pool-info', {"address": "0xc4ad29ba4b3c580e6d59105fff484999997675ff"})

        # Pool Curve.fi USD-BTC-ETH 0xd51a44d3fae010294c616388b506acda1bfaae46
        self.run_model('curve-fi.pool-info', {"address": "0xd51a44d3fae010294c616388b506acda1bfaae46"})

        # Pool: Curve.fi ETH/aETH (ankrCRV) 0xa96a65c051bf88b4095ee1f2451c2a9d43f53ae2
        self.run_model('curve-fi.pool-info', {"address": "0xa96a65c051bf88b4095ee1f2451c2a9d43f53ae2"})
        # Curve.fi ETH/aETH (ankrCRV) Token: 0xaA17A236F2bAdc98DDc0Cf999AbB47D47Fc0A6Cf
        self.run_model('curve-fi.pool-info', {"address": "0xaA17A236F2bAdc98DDc0Cf999AbB47D47Fc0A6Cf"})

        # Curve.fi : 0xdc24316b9ae028f1497c275eb9192a3ea0f67022
        self.run_model('curve-fi.pool-info', {"address": "0xdc24316b9ae028f1497c275eb9192a3ea0f67022"})

        # Curve.fi : 0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6
        self.run_model('curve-fi.pool-info', {"address": "0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6"})

        # Curve.fi renBTC/wBTC: 0x93054188d876f558f4a66b2ef1d97d16edf0895b
        self.run_model('curve-fi.pool-info', {"address": "0x93054188d876f558f4a66b2ef1d97d16edf0895b"})

        # Curve.fi Factory USD Metapool: Alchemix USD: 0x43b4FdFD4Ff969587185cDB6f0BD875c5Fc83f8c
        # curve-fi.pool-info-tokens
        self.run_model('curve-fi.pool-info', {"address": "0x43b4fdfd4ff969587185cdb6f0bd875c5fc83f8c"})

        # Curve.fi DAI/USDC/USDT 0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7
        self.run_model('curve-fi.pool-info', {"address": "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"})
        # ${curve_pool_info_tvl}
        self.run_model('curve-fi.pool-tvl', {"address": "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"})

        # Curve.fi USD-BTC-ETH
        self.run_model('curve-fi.pool-info', {"address": "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46"})

        # Curve.fi ETH/rETH 0xF9440930043eb3997fc70e1339dBb11F341de7A8
        self.run_model('curve-fi.pool-info', {"address": "0xF9440930043eb3997fc70e1339dBb11F341de7A8"})

        # Curve.fi Curve.fi ETH/rETH (rCRV) LP: 0x53a901d48795C58f485cBB38df08FA96a24669D5
        self.run_model('curve-fi.pool-info', {"address": "0x53a901d48795C58f485cBB38df08FA96a24669D5"})

        # Curve.fi Curve.fi ETH/stETH LP: 0x06325440d014e39736583c165c2963ba99faf14e
        self.run_model('curve-fi.pool-info', {"address": "0xDC24316b9AE028F1497c275EB9192a3Ea0f67022"})

        # Curve.fi Factory Plain Pool: cvxCRV (cvxcrv-f)
        self.run_model('curve-fi.pool-info', {"address": "0x9D0464996170c6B9e75eED71c68B99dDEDf279e8"})

        # Curve.fi cyDAI/cyUSDC/cyUSDT 0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF
        self.run_model('curve-fi.pool-info', {"address": "0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF"})

    def test_gauge(self):
        self.title('Curve - Gauge')

        # Curve.fi oBTC/sbtcCRV Gauge Deposit: 0x11137B10C210b579405c21A07489e28F3c040AB1
        # curve-fi.get-gauge-stake-and-claimable-rewards
        self.run_model('curve-fi.gauge-yield', {"address": "0x11137B10C210b579405c21A07489e28F3c040AB1"})
        # Curve.fi tbtc2/sbtcCRV-f Gauge Deposit: 0x29284d30bcb70e86a6c3f84cbc4de0ce16b0f1ca
        # curve-fi.get-gauge-stake-and-claimable-rewards
        self.run_model('curve-fi.gauge-yield', {"address": "0x29284d30bcb70e86a6c3f84cbc4de0ce16b0f1ca"})  # __all__
        # 0x824F13f1a2F29cFEEa81154b46C0fc820677A637 is Curve.fi rCRV Gauge Deposit (rCRV-gauge)
        self.run_model('curve-fi.all-gauge-claim-addresses', {"address": "0x824F13f1a2F29cFEEa81154b46C0fc820677A637"})
        # 0x72E158d38dbd50A483501c24f792bDAAA3e7D55C is Curve.fi FRAX3CRV-f Gauge Deposit (FRAX3CRV-...)
        self.run_model('curve-fi.all-gauge-claim-addresses', {"address": "0x72E158d38dbd50A483501c24f792bDAAA3e7D55C"})

        # TODO
        # self.run_model('curve-fi.all-gauges', {}' curve-fi.get-gauge-controller

    def test_pool_info(self):
        block_number = 15311050
        curve_pools = ['0x961226b64ad373275130234145b96d100dc0b655',
                        '0x8301AE4fc9c624d1D396cbDAa1ed877821D7C511',
                        '0x43b4FdFD4Ff969587185cDB6f0BD875c5Fc83f8c',
                        '0xd658A338613198204DCa1143Ac3F01A722b5d94A',
                        '0xDC24316b9AE028F1497c275EB9192a3Ea0f67022',
                        '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7',
                        '0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B',
                        '0xCEAF7747579696A2F0bb206a14210e3c9e6fB269',
                        '0xD51a44d3FaE010294C616388b506AcdA1bfAAE46',
                        '0x5a6A4D54456819380173272A5E8E9B9904BdF41B',
                        '0x93054188d876f558f4a66B2EF1d97d16eDf0895B',
                        '0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF',
                        '0x9D0464996170c6B9e75eED71c68B99dDEDf279e8',
                        '0x828b154032950C8ff7CF8085D841723Db2696056',
                        '0x4e0915C88bC70750D68C481540F081fEFaF22273',
                        '0xA5407eAE9Ba41422680e2e00537571bcC53efBfD',]

        for pool_addr in curve_pools:
            self.run_model('curve-fi.pool-info', {"address": pool_addr}, block_number=block_number)
            self.run_model('curve-fi.pool-tvl', {"address": pool_addr}, block_number=block_number)


    def test_lp_token(self):
        block_number = 14830357
        self.title('Curve - Pool Info from LP')
        lp_token_addresses = ['0xD905e2eaeBe188fc92179b6350807D8bd91Db0D8',
                              '0xC25a3A3b969415c80451098fa907EC722572917F',
                              '0x3b3ac5386837dc563660fb6a0937dfaa5924333b',
                              '0x845838df265dcd2c412a1dc9e959c7d08537f8a2',
                              '0xdf5e0e81dff6faf3a7e52ba697820c5e32d806a8',
                              '0x9fC689CCaDa600B6DF723D9E47D84d76664a1F23',
                              '0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3',
                              '0x49849C98ae39Fff122806C06791Fa73784FB3675',
                              '0x1AEf73d49Dedc4b1778d0706583995958Dc862e6',
                              '0x6D65b498cb23deAba52db31c93Da9BFFb340FB8F',
                              '0x4f3E8F405CF5aFC05D68142F3783bDfE13811522',
                              '0x97E2768e8E73511cA874545DC5Ff8067eB19B787',
                              '0x5B5CFE992AdAC0C9D48E05854B2d91C73a003858',
                              '0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490']

        for lp_addr in lp_token_addresses:
            self.run_model('curve-fi.pool-info', {"address": lp_addr}, block_number=block_number)
            self.run_model('curve-fi.pool-tvl', {"address": lp_addr}, block_number=block_number)

    def test_convex(self):
        self.title('Curve - Convex')
        self.run_model('convex-fi.all-pool-info', {})
        self.run_model('convex-fi.earned', {'address': '0x5291fBB0ee9F51225f0928Ff6a83108c86327636'})
