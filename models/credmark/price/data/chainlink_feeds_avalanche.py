from credmark.cmf.types import Address

# The native token on other chain, give a direct address of feed.
# TODO: find the token address so to find the feed in Chainlink's registry
CHAINLINK_OVERRIDE_FEED_AVALANCHE = {
    # AAVE / USD
    Address('0x63a72806098bd3d9520cc43356dd78afe5d386d9'):
    {'feed': {'address': '0xcb7f6eF54bDc05B704a0aCf604A6A16C53d359e1'},
     'quote': {'symbol': 'USD'}},
    # ALPHA / USD
    Address('0x9c3254bb4f7f6a05a4aaf2cadce592c848d043c1'):
    {'feed': {'address': '0x9C81461B6B821407E0a2968F9CEc23e3C7063F84'},
     'quote': {'symbol': 'USD'}},
    # AMPL / USD
    Address('0x027dbca046ca156de9622cd1e2d907d375e53aa7'):
    {'feed': {'address': '0x9e107262620CfC6E0e2445df6C0ca0a9aD9Ba627'},
     'quote': {'symbol': 'USD'}},
    # BAT / USD
    Address('0x98443b96ea4b0858fdf3219cd13e98c7a4690588'):
    {'feed': {'address': '0x553BDc8a55569756Bd4bAB24e545752474A2Cd5a'},
     'quote': {'symbol': 'USD'}},
    # BTC / USD
    Address('0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'):
    {'feed': {'address': '0x154baB1FC1D87fF641EeD0E9Bc0f8a50D880D2B6'},
     'quote': {'symbol': 'USD'}},
    # BUSD / USD
    Address('0x9c9e5fd8bbc25984b178fdce6117defa39d2db39'):
    {'feed': {'address': '0x9Cb8E5EA1404d5012C0fc01B7B927AE6Aa09164f'},
     'quote': {'symbol': 'USD'}},
    # CAKE / USD
    Address('0x98a4d09036cc5337810096b1d004109686e56afc'):
    {'feed': {'address': '0x0aCcDFd55026873CB12F75f66513b42fB4974245'},
     'quote': {'symbol': 'USD'}},
    # COMP / USD
    Address('0xc3048e19e76cb9a3aa9d77d8c03c29fc906e2437'):
    {'feed': {'address': '0x498A8B3E1B7582Ae3Ca3ae22AC544a02dB86D4c5'},
     'quote': {'symbol': 'USD'}},
    # CRV / USD
    Address('0x249848beca43ac405b8102ec90dd5f22ca513c06'):
    {'feed': {'address': '0xFf6e2c3C9E9a174824a764dbb8222454f6A3ecb1'},
     'quote': {'symbol': 'USD'}},
    # DAI / USD
    Address('0xd586e7f844cea2f87f50152665bcbc2c279d8d70'):
    {'feed': {'address': '0xCC4633a1a85d553623bAC7945Bd87CFad6E6a8c8'},
     'quote': {'symbol': 'USD'}},
    # ETH / USD
    Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
    {'feed': {'address': '0xEfaa69f461E0aaf0be1798b01371Daf14AC55eA8'},
     'quote': {'symbol': 'USD'}},
    # FRAX / USD
    Address('0xd24c2ad096400b6fbcd2ad8b24e7acbc21a1da64'):
    {'feed': {'address': '0x5eDC2538E11b67cf93ED145b04E5E457d9F9Cc0B'},
     'quote': {'symbol': 'USD'}},
    # FXS / USD
    Address('0x214db107654ff987ad859f34125307783fc8e387'):
    {'feed': {'address': '0x92398CAF00D65e9A63b5d50D1CBD53223137A400'},
     'quote': {'symbol': 'USD'}},
    # GMX / USD
    Address('0x62edc0692bd897d2295872a9ffcac5425011c661'):
    {'feed': {'address': '0x3Ec39652e73337350a712Fb418DBb4C2a8247673'},
     'quote': {'symbol': 'USD'}},
    # JOE / USD
    Address('0x6e84a6216ea6dacc71ee8e6b0a5b7322eebc0fdd'):
    {'feed': {'address': '0x15811F91fAb76Bd240CAeC783a32f1BAAE41c513'},
     'quote': {'symbol': 'USD'}},
    # KNC / USD
    Address('0x39fc9e94caeacb435842fadedecb783589f50f5f'):
    {'feed': {'address': '0x5474cFC8E5Fa684728bAABBFC95B161134c32758'},
     'quote': {'symbol': 'USD'}},
    # LINK / USD
    Address('0x5947bb275c521040051d82396192181b413227a3'):
    {'feed': {'address': '0xA2e5d3254F7d6E8C051Afb7F2aeea0dABf21F750'},
     'quote': {'symbol': 'USD'}},
    # MATIC / USD
    Address('0xa56b1b9f4e5a1a1e0868f5fd4352ce7cdf0c2a4f'):
    {'feed': {'address': '0x92655bd2627C17D36b35f20dA3F4A4084E0ABd6F'},
     'quote': {'symbol': 'USD'}},
    # MIM / USD
    Address('0x130966628846bfd36ff31a822705796e8cb8c18d'):
    {'feed': {'address': '0x9D0aabA64B0BA4650419a37D14175dA05471793c'},
     'quote': {'symbol': 'USD'}},
    # MIMATIC / USD
    Address('0x3b55e45fd6bd7d4724f5c47e0d1bcaedd059263e'):
    {'feed': {'address': '0x5aF11EEC59e1BaC3F4e2565621B43Cfbe748e698'},
     'quote': {'symbol': 'USD'}},
    # MKR / USD
    Address('0x88128fd4b259552a9a1d457f435a6527aab72d42'):
    {'feed': {'address': '0xB3752dC7c1D71A1B381925EC5e6bbf2950519Aa2'},
     'quote': {'symbol': 'USD'}},
    # QI / USD
    Address('0x8729438eb15e2c8b576fcc6aecda6a148776c0f5'):
    {'feed': {'address': '0x4bc3BeBb7eB60155f8b38771D9926d9A23dad5B5'},
     'quote': {'symbol': 'USD'}},
    # SNX / USD
    Address('0xbec243c995409e6520d7c41e404da5deba4b209b'):
    {'feed': {'address': '0xF01826625694D04A30285355A5F3aEf567E6F676'},
     'quote': {'symbol': 'USD'}},
    # SPELL / USD
    Address('0xce1bffbd5374dac86a2893119683f4911a2f7814'):
    {'feed': {'address': '0x0a58227E7D7A8175E4F5f8a0D32968d153B9ce59'},
     'quote': {'symbol': 'USD'}},
    # SUSHI / USD
    Address('0x37b608519f91f70f2eeb0e5ed9af4061722e4f76'):
    {'feed': {'address': '0xdE672241200B9309f86AB79fd082423f32fD8f0D'},
     'quote': {'symbol': 'USD'}},
    # TUSD / USD
    Address('0x1c20e891bab6b1727d14da358fae2984ed9b59eb'):
    {'feed': {'address': '0x2EBa2C3CDF50f5BC20fc23F533B227dB6b10A725'},
     'quote': {'symbol': 'USD'}},
    # UNI / USD
    Address('0x8ebaf22b6f053dffeaf46f4dd9efa95d89ba8580'):
    {'feed': {'address': '0xA0326D3AD91D7724380c096AA62Ae1d5A8d260A8'},
     'quote': {'symbol': 'USD'}},
    # USDC / USD
    Address('0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e'):
    {'feed': {'address': '0xfBd998938f8f7210eEC3D1e12E80A10972F02aEd'},
     'quote': {'symbol': 'USD'}},
    # USDT / USD
    Address('0x9702230a8ea53601f5cd2dc00fdbc13d4df4a8c7'):
    {'feed': {'address': '0xb8AEB9160385fa2D1B63B5E88351238593ba0127'},
     'quote': {'symbol': 'USD'}},
    # UST / USD
    Address('0xb599c3590f42f8f995ecfa0f85d2980b76862fc1'):
    {'feed': {'address': '0xa01516869D8325Fd18a77b307cA38Cab1Eb8Fdeb'},
     'quote': {'symbol': 'USD'}},
    # WBTC / USD
    Address('0x50b7545627a5162f82a992c33b87adc75187b218'):
    {'feed': {'address': '0xb50D5dB75a844365995C29B534a31536a4C56513'},
     'quote': {'symbol': 'USD'}},
    # WOO / ETH
    Address('0xabc9547b534519ff73921b1fba6e672b5f58d083'):
    {'feed': {'address': '0x6339dfD6433C305661B060659922a70fC4eEbAC6'},
     'quote': {'symbol': 'ETH'}},
    # XAVA / USD
    Address('0xd1c3f94de7e5b45fa4edbba472491a9f4b166fc4'):
    {'feed': {'address': '0x1872758F3635aa3CFA58CA30Bc2Ec84e5A2C493F'},
     'quote': {'symbol': 'USD'}},
    # YFI / USD
    Address('0x9eaac1b23d935365bd7b542fe22ceee2922f52dc'):
    {'feed': {'address': '0x27355dF92298c785440a4D16574DF736Eb0627d0'},
     'quote': {'symbol': 'USD'}},
    # ZRX / USD
    Address('0x596fa47043f99a4e0f122243b841e55375cde0d2'):
    {'feed': {'address': '0x347F6cdbD9514284b301456956c846b7B21F375B'},
     'quote': {'symbol': 'USD'}}
}
