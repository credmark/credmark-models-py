from credmark.cmf.types import Address

# The native token on other chain, give a direct address of feed.
CHAINLINK_OVERRIDE_FEED_OPTIMISM = {
    # AAVE / USD
    Address('0x76fb31fb4af56892a25e32cfc43de717950c9278'):
    {'feed': {'address': '0x338ed6787f463394D24813b297401B9F05a8C9d1'},
        'quote': {'symbol': 'USD'}},
    # BAL / USD
    Address('0xfe8b128ba8c78aabc59d4c64cee7ff28e9379921'):
    {'feed': {'address': '0x30D9d31C1ac29Bc2c2c312c1bCa9F8b3D60e2376'},
        'quote': {'symbol': 'USD'}},
    # BOND / USD
    Address('0x3e7ef8f50246f725885102e8238cbba33f276747'):
    {'feed': {'address': '0x8fCfb87fc17CfD5775d234AcFd1753764899Bf20'},
        'quote': {'symbol': 'USD'}},
    # BTC / USD
    Address('0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'):
    {'feed': {'address': '0xD702DD976Fb76Fffc2D3963D037dfDae5b04E593'},
        'quote': {'symbol': 'USD'}},
    # BUSD / USD
    Address('0x9c9e5fd8bbc25984b178fdce6117defa39d2db39'):
    {'feed': {'address': '0xC1cB3b7cbB3e786aB85ea28489f332f4FAEd5Bc4'},
        'quote': {'symbol': 'USD'}},
    # CBETH / ETH
    Address('0xaddb6a0412de1ba0f936dcaeb8aaa24578dcf3b2'):
    {'feed': {'address': '0x138b809B8472fF09Cd3E075E6EcbB2e42D41d870'},
        'quote': {'symbol': 'ETH'}},
    # CRV / USD
    Address('0x0994206dfe8de6ec6920ff4d779b0d950605fb53'):
    {'feed': {'address': '0xbD92C6c284271c227a1e0bF1786F468b539f51D9'},
        'quote': {'symbol': 'USD'}},
    # DAI / USD
    Address('0xda10009cbd5d07dd0cecc66161fc93d7c9000da1'):
    {'feed': {'address': '0x8dBa75e83DA73cc766A7e5a0ee71F656BAb470d6'},
        'quote': {'symbol': 'USD'}},
    # ETH / USD
    Address('0xdeaddeaddeaddeaddeaddeaddeaddeaddead0000'):
    {'feed': {'address': '0x13e3Ee699D1909E989722E753853AE30b17e08c5'},
        'quote': {'symbol': 'USD'}},
    # FRAX / USD
    Address('0x2e3d870790dc77a83dd1d18184acc7439a53f475'):
    {'feed': {'address': '0xc7D132BeCAbE7Dcc4204841F33bae45841e41D9C'},
        'quote': {'symbol': 'USD'}},
    # FXS / USD
    Address('0x67ccea5bb16181e7b4109c9c2143c24a1c2205be'):
    {'feed': {'address': '0xB9B16330671067B1b062B9aC2eFd2dB75F03436E'},
        'quote': {'symbol': 'USD'}},
    # KNC / USD
    Address('0xa00e3a3511aac35ca78530c85007afcd31753819'):
    {'feed': {'address': '0xCB24d22aF35986aC1feb8874AdBbDF68f6dC2e96'},
        'quote': {'symbol': 'USD'}},
    # LDO / USD
    Address('0xfdb794692724153d1488ccdbe0c56c252596735f'):
    {'feed': {'address': '0x221618871470f78D8a3391d35B77dFb3C0fbc383'},
        'quote': {'symbol': 'USD'}},
    # LINK / ETH
    Address('0x350a791bfc2c21f9ed5d10980dad2e2638ffa7f6'):
    {'feed': {'address': '0x464A1515ADc20de946f8d0DEB99cead8CEAE310d'},
        'quote': {'symbol': 'ETH'}},
    # LINK / USD
    Address('0x350a791bfc2c21f9ed5d10980dad2e2638ffa7f6'):
    {'feed': {'address': '0xCc232dcFAAE6354cE191Bd574108c1aD03f86450'},
        'quote': {'symbol': 'USD'}},
    # LUSD / USD
    Address('0xc40f949f8a4e094d1b49a23ea9241d289b7b2819'):
    {'feed': {'address': '0x9dfc79Aaeb5bb0f96C6e9402671981CdFc424052'},
        'quote': {'symbol': 'USD'}},
    # OP / USD
    Address('0x4200000000000000000000000000000000000042'):
    {'feed': {'address': '0x0D276FC14719f9292D5C1eA2198673d1f4269246'},
        'quote': {'symbol': 'USD'}},
    # PERP / USD
    Address('0x9e1028f5f1d5ede59748ffcee5532509976840e0'):
    {'feed': {'address': '0xA12CDDd8e986AF9288ab31E58C60e65F2987fB13'},
        'quote': {'symbol': 'USD'}},
    # SNX / USD
    Address('0x8700daec35af8ff88c16bdf0418774cb3d7599b4'):
    {'feed': {'address': '0x2FCF37343e916eAEd1f1DdaaF84458a359b53877'},
        'quote': {'symbol': 'USD'}},
    # SUSD / USD
    Address('0x8c6f28f2f1a3c87f0f938b96d27520d9751ec8d9'):
    {'feed': {'address': '0x7f99817d87baD03ea21E05112Ca799d715730efe'},
        'quote': {'symbol': 'USD'}},
    # UNI / USD
    Address('0x6fd9d7ad17242c41f7131d257212c54a0e816691'):
    {'feed': {'address': '0x11429eE838cC01071402f21C219870cbAc0a59A0'},
        'quote': {'symbol': 'USD'}},
    # USDC / USD
    Address('0x7f5c764cbc14f9669b88837ca1490cca17c31607'):
    {'feed': {'address': '0x16a9FA2FDa030272Ce99B29CF780dFA30361E0f3'},
        'quote': {'symbol': 'USD'}},
    # USDT / USD
    Address('0x94b008aa00579c1307b0ef2c499ad98a8ce58e58'):
    {'feed': {'address': '0xECef79E109e997bCA29c1c0897ec9d7b03647F5E'},
        'quote': {'symbol': 'USD'}},
    # WBTC / USD
    Address('0x68f180fcce6836688e9084f035309e29bf0a2095'):
    {'feed': {'address': '0x718A5788b89454aAE3A028AE9c111A29Be6c2a6F'},
        'quote': {'symbol': 'USD'}},
    # WSTETH / ETH
    Address('0x1f32b1c2345538c0c6f582fcb022739c4a194ebb'):
    {'feed': {'address': '0x524299Ab0987a7c4B3c8022a35669DdcdC715a10'},
        'quote': {'symbol': 'ETH'}},
    # WSTETH / USD
    Address('0x1f32b1c2345538c0c6f582fcb022739c4a194ebb'):
    {'feed': {'address': '0x698B585CbC4407e2D54aa898B2600B53C68958f7'},
        'quote': {'symbol': 'USD'}}
}
