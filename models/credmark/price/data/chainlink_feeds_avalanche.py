from credmark.cmf.types import Address

# The native token on other chain, give a direct address of feed.
CHAINLINK_OVERRIDE_FEED_AVALANCHE = {
    # AAVE / USD
    Address('0x63a72806098bd3d9520cc43356dd78afe5d386d9'):
    {'feed': {'address': '0x3CA13391E9fb38a75330fb28f8cc2eB3D9ceceED'},
        'quote': {'symbol': 'USD'}},
    # ALPHA / USD
    Address('0x9c3254bb4f7f6a05a4aaf2cadce592c848d043c1'):
    {'feed': {'address': '0x7B0ca9A6D03FE0467A31Ca850f5bcA51e027B3aF'},
        'quote': {'symbol': 'USD'}},
    # AMPL / USD
    Address('0x027dbca046ca156de9622cd1e2d907d375e53aa7'):
    {'feed': {'address': '0xcf667FB6Bd30c520A435391c50caDcDe15e5e12f'},
        'quote': {'symbol': 'USD'}},
    # AVAX / USD
    Address('0xaAaAaAaaAaAaAaaAaAAAAAAAAaaaAaAaAaaAaaAa'):
    {'feed': {'address': '0x0A77230d17318075983913bC2145DB16C7366156'},
        'quote': {'symbol': 'USD'}},
    # BAT / USD
    Address('0x98443b96ea4b0858fdf3219cd13e98c7a4690588'):
    {'feed': {'address': '0xe89B3CE86D25599D1e615C0f6a353B4572FF868D'},
        'quote': {'symbol': 'USD'}},
    # BTC / USD
    Address('0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'):
    {'feed': {'address': '0x2779D32d5166BAaa2B2b658333bA7e6Ec0C65743'},
        'quote': {'symbol': 'USD'}},
    # BUSD / USD
    Address('0x9c9e5fd8bbc25984b178fdce6117defa39d2db39'):
    {'feed': {'address': '0x827f8a0dC5c943F7524Dda178E2e7F275AAd743f'},
        'quote': {'symbol': 'USD'}},
    # CAKE / USD
    Address('0x98a4d09036cc5337810096b1d004109686e56afc'):
    {'feed': {'address': '0x79bD0EDd79dB586F22fF300B602E85a662fc1208'},
        'quote': {'symbol': 'USD'}},
    # COMP / USD
    Address('0xc3048e19e76cb9a3aa9d77d8c03c29fc906e2437'):
    {'feed': {'address': '0x9D6AA0AC8c4818433bEA7a74F49C73B57BcEC4Ec'},
        'quote': {'symbol': 'USD'}},
    # CRV / USD
    Address('0x249848beca43ac405b8102ec90dd5f22ca513c06'):
    {'feed': {'address': '0x7CF8A6090A9053B01F3DF4D4e6CfEdd8c90d9027'},
        'quote': {'symbol': 'USD'}},
    # DAI / USD
    Address('0xd586e7f844cea2f87f50152665bcbc2c279d8d70'):
    {'feed': {'address': '0x51D7180edA2260cc4F6e4EebB82FEF5c3c2B8300'},
        'quote': {'symbol': 'USD'}},
    # ETH / USD
    Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
    {'feed': {'address': '0x976B3D034E162d8bD72D6b9C989d545b839003b0'},
        'quote': {'symbol': 'USD'}},
    # FRAX / USD
    Address('0xd24c2ad096400b6fbcd2ad8b24e7acbc21a1da64'):
    {'feed': {'address': '0xbBa56eF1565354217a3353a466edB82E8F25b08e'},
        'quote': {'symbol': 'USD'}},
    # FXS / USD
    Address('0x214db107654ff987ad859f34125307783fc8e387'):
    {'feed': {'address': '0x12Af94c3716bbf339Aa26BfD927DDdE63B27D50C'},
        'quote': {'symbol': 'USD'}},
    # GMX / USD
    Address('0x62edc0692bd897d2295872a9ffcac5425011c661'):
    {'feed': {'address': '0x3F968A21647d7ca81Fb8A5b69c0A452701d5DCe8'},
        'quote': {'symbol': 'USD'}},
    # JOE / USD
    Address('0x6e84a6216ea6dacc71ee8e6b0a5b7322eebc0fdd'):
    {'feed': {'address': '0x02D35d3a8aC3e1626d3eE09A78Dd87286F5E8e3a'},
        'quote': {'symbol': 'USD'}},
    # KNC / USD
    Address('0x39fc9e94caeacb435842fadedecb783589f50f5f'):
    {'feed': {'address': '0x9df2195dc96e6Ef983B1aAC275649F3f28F82Aa1'},
        'quote': {'symbol': 'USD'}},
    # LINK / AVAX
    Address('0x5947bb275c521040051d82396192181b413227a3'):
    {'feed': {'address': '0x1b8a25F73c9420dD507406C3A3816A276b62f56a'},
        'quote': {'symbol': 'AVAX'}},
    # LINK / USD
    Address('0x5947bb275c521040051d82396192181b413227a3'):
    {'feed': {'address': '0x49ccd9ca821EfEab2b98c60dC60F518E765EDe9a'},
        'quote': {'symbol': 'USD'}},
    # MATIC / USD
    Address('0xa56b1b9f4e5a1a1e0868f5fd4352ce7cdf0c2a4f'):
    {'feed': {'address': '0x1db18D41E4AD2403d9f52b5624031a2D9932Fd73'},
        'quote': {'symbol': 'USD'}},
    # MIM / USD
    Address('0x130966628846bfd36ff31a822705796e8cb8c18d'):
    {'feed': {'address': '0x54EdAB30a7134A16a54218AE64C73e1DAf48a8Fb'},
        'quote': {'symbol': 'USD'}},
    # MIMATIC / USD
    Address('0x3b55e45fd6bd7d4724f5c47e0d1bcaedd059263e'):
    {'feed': {'address': '0x5D1F504211c17365CA66353442a74D4435A8b778'},
        'quote': {'symbol': 'USD'}},
    # MKR / USD
    Address('0x88128fd4b259552a9a1d457f435a6527aab72d42'):
    {'feed': {'address': '0x3E54eB0475051401D093702A5DB84EFa1Ab77b14'},
        'quote': {'symbol': 'USD'}},
    # QI / USD
    Address('0x8729438eb15e2c8b576fcc6aecda6a148776c0f5'):
    {'feed': {'address': '0x36E039e6391A5E7A7267650979fdf613f659be5D'},
        'quote': {'symbol': 'USD'}},
    # SNX / USD
    Address('0xbec243c995409e6520d7c41e404da5deba4b209b'):
    {'feed': {'address': '0x01752eAAB988ECb0ceBa2C8FC97c4f1d38Bf246D'},
        'quote': {'symbol': 'USD'}},
    # SPELL / USD
    Address('0xce1bffbd5374dac86a2893119683f4911a2f7814'):
    {'feed': {'address': '0x4F3ddF9378a4865cf4f28BE51E10AECb83B7daeE'},
        'quote': {'symbol': 'USD'}},
    # SUSHI / USD
    Address('0x37b608519f91f70f2eeb0e5ed9af4061722e4f76'):
    {'feed': {'address': '0x449A373A090d8A1e5F74c63Ef831Ceff39E94563'},
        'quote': {'symbol': 'USD'}},
    # TUSD / USD
    Address('0x1c20e891bab6b1727d14da358fae2984ed9b59eb'):
    {'feed': {'address': '0x9Cf3Ef104A973b351B2c032AA6793c3A6F76b448'},
        'quote': {'symbol': 'USD'}},
    # UNI / USD
    Address('0x8ebaf22b6f053dffeaf46f4dd9efa95d89ba8580'):
    {'feed': {'address': '0x9a1372f9b1B71B3A5a72E092AE67E172dBd7Daaa'},
        'quote': {'symbol': 'USD'}},
    # USDC / USD
    Address('0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e'):
    {'feed': {'address': '0xF096872672F44d6EBA71458D74fe67F9a77a23B9'},
        'quote': {'symbol': 'USD'}},
    # USDT / USD
    Address('0x9702230a8ea53601f5cd2dc00fdbc13d4df4a8c7'):
    {'feed': {'address': '0xEBE676ee90Fe1112671f19b6B7459bC678B67e8a'},
        'quote': {'symbol': 'USD'}},
    # UST / USD
    Address('0xb599c3590f42f8f995ecfa0f85d2980b76862fc1'):
    {'feed': {'address': '0xf58B78581c480caFf667C63feDd564eCF01Ef86b'},
        'quote': {'symbol': 'USD'}},
    # WBTC / USD
    Address('0x50b7545627a5162f82a992c33b87adc75187b218'):
    {'feed': {'address': '0x86442E3a98558357d46E6182F4b262f76c4fa26F'},
        'quote': {'symbol': 'USD'}},
    # WOO / ETH
    Address('0xabc9547b534519ff73921b1fba6e672b5f58d083'):
    {'feed': {'address': '0xfAa665F5a0e13beea63b6DfF601DD634959690Df'},
        'quote': {'symbol': 'ETH'}},
    # XAVA / USD
    Address('0xd1c3f94de7e5b45fa4edbba472491a9f4b166fc4'):
    {'feed': {'address': '0x4Cf57DC9028187b9DAaF773c8ecA941036989238'},
        'quote': {'symbol': 'USD'}},
    # YFI / USD
    Address('0x9eaac1b23d935365bd7b542fe22ceee2922f52dc'):
    {'feed': {'address': '0x28043B1Ebd41860B93EC1F1eC19560760B6dB556'},
        'quote': {'symbol': 'USD'}},
    # ZRX / USD
    Address('0x596fa47043f99a4e0f122243b841e55375cde0d2'):
    {'feed': {'address': '0xC07CDf938aa113741fB639bf39699926123fB58B'},
        'quote': {'symbol': 'USD'}}
}
