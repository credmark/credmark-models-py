from credmark.cmf.types import Address

# The native token on other chain, give a direct address of feed.
CHAINLINK_OVERRIDE_FEED_OPTIMISM = {
    # AAVE / USD
    Address('0x76fb31fb4af56892a25e32cfc43de717950c9278'):
    {'feed': {'address': '0x81cC0c227BF9bFB8088b14755DfcA65f7892203b'},
     'quote': {'symbol': 'USD'}},
    # BAL / USD
    Address('0xfe8b128ba8c78aabc59d4c64cee7ff28e9379921'):
    {'feed': {'address': '0x44f690526B76D91072fb0427B0A24b882E612455'},
     'quote': {'symbol': 'USD'}},
    # BOND / USD
    Address('0x3e7ef8f50246f725885102e8238cbba33f276747'):
    {'feed': {'address': '0x3b06B9b3ead7Ec34AE67E2D7f73B128dA09C583a'},
     'quote': {'symbol': 'USD'}},
    # BTC / USD
    Address('0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'):
    {'feed': {'address': '0x0C1272d2aC652D10d03bb4dEB0D31F15ea3EAb2b'},
     'quote': {'symbol': 'USD'}},
    # BUSD / USD
    Address('0x9c9e5fd8bbc25984b178fdce6117defa39d2db39'):
    {'feed': {'address': '0xD24E1CdD2F9c0A070F73081B5f79BdD0d42EFA2f'},
     'quote': {'symbol': 'USD'}},
    # CRV / USD
    Address('0x0994206dfe8de6ec6920ff4d779b0d950605fb53'):
    {'feed': {'address': '0x7c56d3650f9aCD992b3Aa635C04A311c54Ad264c'},
     'quote': {'symbol': 'USD'}},
    # DAI / USD
    Address('0xda10009cbd5d07dd0cecc66161fc93d7c9000da1'):
    {'feed': {'address': '0xbCe7579e241e5d676c2371Dc21891489dAcDA250'},
     'quote': {'symbol': 'USD'}},
    # ETH / USD
    Address('0xdeaddeaddeaddeaddeaddeaddeaddeaddead0000'):
    {'feed': {'address': '0x02f5E9e9dcc66ba6392f6904D5Fcf8625d9B19C9'},
     'quote': {'symbol': 'USD'}},
    # FRAX / USD
    Address('0x2e3d870790dc77a83dd1d18184acc7439a53f475'):
    {'feed': {'address': '0xaB544FDAD5F68f0F8e53284f942D76177635A3D6'},
     'quote': {'symbol': 'USD'}},
    # FXS / USD
    Address('0x67ccea5bb16181e7b4109c9c2143c24a1c2205be'):
    {'feed': {'address': '0xc2212835DE6cb9Ef5e26b04E64f7798472Ff2812'},
     'quote': {'symbol': 'USD'}},
    # KNC / USD
    Address('0xa00e3a3511aac35ca78530c85007afcd31753819'):
    {'feed': {'address': '0xe4391393205B6265585250E7A026103a0D1E168d'},
     'quote': {'symbol': 'USD'}},
    # LINK / ETH
    Address('0x350a791bfc2c21f9ed5d10980dad2e2638ffa7f6'):
    {'feed': {'address': '0xE67a10DA53Fcd59fae7e47F155c290cb5Defb4B0'},
     'quote': {'symbol': 'ETH'}},
    # LUSD / USD
    Address('0xc40f949f8a4e094d1b49a23ea9241d289b7b2819'):
    {'feed': {'address': '0x19dC743a5E9a73eefAbA7047C7CEeBc650F37336'},
     'quote': {'symbol': 'USD'}},
    # OP / USD
    Address('0x4200000000000000000000000000000000000042'):
    {'feed': {'address': '0x4F6dFDFd4d68F68b2692E79f9e94796fC8015770'},
     'quote': {'symbol': 'USD'}},
    # PERP / USD
    Address('0x9e1028f5f1d5ede59748ffcee5532509976840e0'):
    {'feed': {'address': '0xE18a4E99F019F92CD72E0C7C05599d76a89296Cd'},
     'quote': {'symbol': 'USD'}},
    # SNX / USD
    Address('0x8700daec35af8ff88c16bdf0418774cb3d7599b4'):
    {'feed': {'address': '0x584F57911b6EEDab5503E202f8e193663c9bd3DB'},
     'quote': {'symbol': 'USD'}},
    # SUSD / USD
    Address('0x8c6f28f2f1a3c87f0f938b96d27520d9751ec8d9'):
    {'feed': {'address': '0x17D582034c038BaEb17A9E2A969d06f550d3586b'},
     'quote': {'symbol': 'USD'}},
    # UNI / USD
    Address('0x6fd9d7ad17242c41f7131d257212c54a0e816691'):
    {'feed': {'address': '0x85A48ded8c35d82f8f29844e25dD51a70a23c93d'},
     'quote': {'symbol': 'USD'}},
    # USDC / USD
    Address('0x7f5c764cbc14f9669b88837ca1490cca17c31607'):
    {'feed': {'address': '0xd1Cb03cc31caa72D34dba7eBE21897D9580c4AF0'},
     'quote': {'symbol': 'USD'}},
    # USDT / USD
    Address('0x94b008aa00579c1307b0ef2c499ad98a8ce58e58'):
    {'feed': {'address': '0xAc37790fF4aBf9483fAe2D1f62fC61fE6b8E4789'},
     'quote': {'symbol': 'USD'}},
    # WBTC / USD
    Address('0x68f180fcce6836688e9084f035309e29bf0a2095'):
    {'feed': {'address': '0x65F2c716937FB44b2C28417A7AfC2DACcF1C2D61'},
     'quote': {'symbol': 'USD'}},
    # WSTETH / USD
    Address('0x1f32b1c2345538c0c6f582fcb022739c4a194ebb'):
    {'feed': {'address': '0x0d110cC7876d73c3C4190324bCF4C59416bBD259'},
     'quote': {'symbol': 'USD'}}
}
