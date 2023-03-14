from credmark.cmf.types import Address, Network
# The native token on other chain, give a direct address of feed.
# TODO: find the token address so to find the feed in Chainlink's registry
CHAINLINK_OVERRIDE_FEED = {
    Network.Mainnet: {
        # WAVAX: avax-usd.data.eth
        Address('0x85f138bfEE4ef8e540890CFb48F620571d67Eda3'):
        {'ens': {'domain': 'avax-usd.data.eth'},
            'quote': {'symbol': 'USD'}},
        # WSOL: sol-usd.data.eth
        Address('0xD31a59c85aE9D8edEFeC411D448f90841571b89c'):
        {'ens': {'domain': 'sol-usd.data.eth'},
            'quote': {'symbol': 'USD'}},
        # BNB: bnb-usd.data.eth
        Address('0xB8c77482e45F1F44dE1745F52C74426C631bDD52'):
        {'ens': {'domain': 'bnb-usd.data.eth'},
            'quote': {'symbol': 'USD'}},
        # WCELO:
        Address('0xE452E6Ea2dDeB012e20dB73bf5d3863A3Ac8d77a'):
        {'ens': {'domain': 'celo-usd.data.eth'},
            'quote': {'symbol': 'USD'}},
        # BTM
        Address('0xcb97e65f07da24d46bcdd078ebebd7c6e6e3d750'):
        {'ens': {'domain': 'btm-usd.data.eth'},
            'quote': {'symbol': 'USD'}},
        # IOST
        Address('0xfa1a856cfa3409cfa145fa4e20eb270df3eb21ab'):
        {'ens': {'domain': 'iost-usd.data.eth'},
            'quote': {'symbol': 'USD'}},
        # WBTC: only with BTC for WBTC/BTC
        Address('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'):
        {'ens': {'domain': 'wbtc-btc.data.eth'},
            'quote': {'symbol': 'BTC'}},
    },
    Network.BSC: {
        # 1INCH / USD
        Address('0x111111111117dc0aa78b770fa6a738034120c302'):
        {'feed': {'address': '0x9a177bb9f5b6083e962f9e62bd21d4b5660aeb03'},
            'quote': {'symbol': 'USD'}},
        # ADA / USD
        Address('0x3ee2200efb3400fabb9aacf31297cbdd1d435d47'):
        {'feed': {'address': '0xa767f745331d267c7751297d982b050c93985627'},
            'quote': {'symbol': 'USD'}},
        # ALPACA / USD
        Address('0x8f0528ce5ef7b51152a59745befdd91d97091d2f'):
        {'feed': {'address': '0xe0073b60833249ffd1bb2af809112c2fbf221df6'},
            'quote': {'symbol': 'USD'}},
        # ALPHA / BNB
        Address('0xa1faa113cbe53436df28ff0aee54275c13b40975'):
        {'feed': {'address': '0x7bc032a7c19b1bdcb981d892854d090cfb0f238e'},
            'quote': {'symbol': 'BNB'}},
        # ATOM / USD
        Address('0x0eb3a705fc54725037cc9e008bdede697f62f335'):
        {'feed': {'address': '0xb056b7c804297279a9a673289264c17e6dc6055d'},
            'quote': {'symbol': 'USD'}},
        # AUTO / USD
        Address('0xa184088a740c695e156f91f5cc086a06bb78b827'):
        {'feed': {'address': '0x88e71e6520e5ac75f5338f5f0c9ded9d4f692cda'},
            'quote': {'symbol': 'USD'}},
        # AVAX / USD
        Address('0x1ce0c2827e2ef14d5c4f29a091d735a204794041'):
        {'feed': {'address': '0x5974855ce31ee8e1fff2e76591cbf83d7110f151'},
            'quote': {'symbol': 'USD'}},
        # AXS / USD
        Address('0x715d400f88c167884bbcc41c5fea407ed4d2f8a0'):
        {'feed': {'address': '0x7b49524ee5740c99435f52d731dfc94082fe61ab'},
            'quote': {'symbol': 'USD'}},
        # BAND / USD
        Address('0xad6caeb32cd2c308980a548bd0bc5aa4306c6c18'):
        {'feed': {'address': '0xc78b99ae87ff43535b0c782128db3cb49c74a4d3'},
            'quote': {'symbol': 'USD'}},
        # BCH / USD
        Address('0x8ff795a6f4d97e7887c79bea79aba5cc76444adf'):
        {'feed': {'address': '0x43d80f616daf0b0b42a928eed32147dc59027d41'},
            'quote': {'symbol': 'USD'}},
        # BETH / USD
        Address('0x250632378e573c6be1ac2f97fcdf00515d0aa91b'):
        {'feed': {'address': '0x2a3796273d47c4ed363b361d3aefb7f7e2a13782'},
            'quote': {'symbol': 'USD'}},
        # BIFI / USD
        Address('0xca3f508b8e4dd382ee878a314789373d80a5190a'):
        {'feed': {'address': '0xab827b69dacd586a37e80a7d552a4395d576e645'},
            'quote': {'symbol': 'USD'}},
        # BNB / USD
        Address('0x0000000000000000010000100100111001000010'):
        {'feed': {'address': '0x0567f2323251f0aab15c8dfb1967e4e8a7d42aee'},
            'quote': {'symbol': 'USD'}},
        # BSW / USD
        Address('0x965f527d9159dce6288a2219db51fc6eef120dd1'):
        {'feed': {'address': '0x08e70777b982a58d23d05e3d7714f44837c06a21'},
            'quote': {'symbol': 'USD'}},
        # BTT / USD
        Address('0x352cb5e19b12fc216548a2677bd0fce83bae434b'):
        {'feed': {'address': '0x4d82c300d699d70a932bd2d556124765a6872d6e'},
            'quote': {'symbol': 'USD'}},
        # BUSD / USD
        Address('0xe9e7cea3dedca5984780bafc599bd69add087d56'):
        {'feed': {'address': '0xcbb98864ef56e9042e7d2efef76141f15731b82f'},
            'quote': {'symbol': 'USD'}},
        # C98 / USD
        Address('0xaec945e04baf28b135fa7c640f624f8d90f1c3a6'):
        {'feed': {'address': '0x889158e39628c0397dc54b84f6b1cbe0aaeb7ffc'},
            'quote': {'symbol': 'USD'}},
        # CAKE / USD
        Address('0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82'):
        {'feed': {'address': '0xb6064ed41d4f67e353768aa239ca86f4f73665a1'},
            'quote': {'symbol': 'USD'}},
        # COMP / USD
        Address('0x52ce071bd9b1c4b00a0b92d298c512478cad67e8'):
        {'feed': {'address': '0x0db8945f9aef5651fa5bd52314c5aae78dfde540'},
            'quote': {'symbol': 'USD'}},
        # CREAM / USD
        Address('0xd4cb328a82bdf5f03eb737f37fa6b370aef3e888'):
        {'feed': {'address': '0xa12fc27a873cf114e6d8bbaf8bd9b8ac56110b39'},
            'quote': {'symbol': 'USD'}},
        # DAI / USD
        Address('0x1af3f329e8be154074d8769d1ffa4ee058b1dbc3'):
        {'feed': {'address': '0x132d3c0b1d2cea0bc552588063bdbb210fdeecfa'},
            'quote': {'symbol': 'USD'}},
        # DF / USD
        Address('0x4a9a2b2b04549c3927dd2c9668a5ef3fca473623'):
        {'feed': {'address': '0x1b816f5e122efa230300126f97c018716c4e47f5'},
            'quote': {'symbol': 'USD'}},
        # DODO / USD
        Address('0x67ee3cb086f8a16f34bee3ca72fad36f7db929e2'):
        {'feed': {'address': '0x87701b15c08687341c2a847ca44ecfbc8d7873e1'},
            'quote': {'symbol': 'USD'}},
        # DOGE / USD
        Address('0xba2ae424d960c26247dd6c32edc70b295c744c43'):
        {'feed': {'address': '0x3ab0a0d137d4f946fbb19eecc6e92e64660231c8'},
            'quote': {'symbol': 'USD'}},
        # DOT / USD
        Address('0x7083609fce4d1d8dc0c979aab8c869ea2c873402'):
        {'feed': {'address': '0xc333eb0086309a16aa7c8308dfd32c8bba0a2592'},
            'quote': {'symbol': 'USD'}},
        # EOS / USD
        Address('0x56b6fb708fc5732dec1afc8d8556423a2edccbd6'):
        {'feed': {'address': '0xd5508c8ffdb8f15ce336e629fd4ca9adb48f50f0'},
            'quote': {'symbol': 'USD'}},
        # ETH / USD
        Address('0x2170ed0880ac9a755fd29b2688956bd959f933f8'):
        {'feed': {'address': '0x9ef1b8c0e4f7dc8bf5719ea496883dc6401d5b2e'},
            'quote': {'symbol': 'USD'}},
        # FRAX / USD
        Address('0x90c97f71e18723b0cf0dfa30ee176ab653e89f40'):
        {'feed': {'address': '0x13a9c98b07f098c5319f4ff786eb16e22dc738e1'},
            'quote': {'symbol': 'USD'}},
        # FTM / USD
        Address('0xad29abb318791d579433d831ed122afeaf29dcfe'):
        {'feed': {'address': '0xe2a47e87c0f4134c8d06a41975f6860468b2f925'},
            'quote': {'symbol': 'USD'}},
        # FXS / USD
        Address('0xe48a3d7d0bc88d552f730b62c006bc925eadb9ee'):
        {'feed': {'address': '0x0e9d55932893fb1308882c7857285b2b0bcc4f4a'},
            'quote': {'symbol': 'USD'}},
        # GMT / USD
        Address('0x7ddc52c4de30e94be3a6a0a2b259b2850f421989'):
        {'feed': {'address': '0x8b0d36ae4cf8e277773a7ba5f35c09edb144241b'},
            'quote': {'symbol': 'USD'}},
        # KNC / USD
        Address('0xfe56d5892bdffc7bf58f2e84be1b2c32d21c308b'):
        {'feed': {'address': '0xf2f8273f6b9fc22c90891dc802caf60eef805cdf'},
            'quote': {'symbol': 'USD'}},
        # LINA / USD
        Address('0x762539b45a1dcce3d36d080f74d1aed37844b878'):
        {'feed': {'address': '0x38393201952f2764e04b290af9df427217d56b41'},
            'quote': {'symbol': 'USD'}},
        # LINK / USD
        Address('0xf8a0bf9cf54bb92f17374d9e9a321e6a111a51bd'):
        {'feed': {'address': '0xca236e327f629f9fc2c30a4e95775ebf0b89fac8'},
            'quote': {'symbol': 'USD'}},
        # LIT / USD
        Address('0xb59490ab09a0f526cc7305822ac65f2ab12f9723'):
        {'feed': {'address': '0x83766ba8d964feaed3819b145a69c947df9cb035'},
            'quote': {'symbol': 'USD'}},
        # LTC / USD
        Address('0x4338665cbb7b2485a8855a139b75d5e34ab0db94'):
        {'feed': {'address': '0x74e72f37a8c415c8f1a98ed42e78ff997435791d'},
            'quote': {'symbol': 'USD'}},
        # MATIC / USD
        Address('0xcc42724c6683b7e57334c4e856f4c9965ed682bd'):
        {'feed': {'address': '0x7ca57b0ca6367191c94c8914d7df09a57655905f'},
            'quote': {'symbol': 'USD'}},
        # MDX / USD
        Address('0x9c65ab58d8d978db963e63f2bfb7121627e3a739'):
        {'feed': {'address': '0x9165366bf450a6906d25549f0e0f8e6586fc93e2'},
            'quote': {'symbol': 'USD'}},
        # MIR / USD
        Address('0x5b6dcf557e2abe2323c48445e8cc948910d8c2c9'):
        {'feed': {'address': '0x291b2983b995870779c36a102da101f8765244d6'},
            'quote': {'symbol': 'USD'}},
        # NEAR / USD
        Address('0x1fa4a73a3f0133f0025378af00236f3abdee5d63'):
        {'feed': {'address': '0x0fe4d87883005fcafaf56b81d09473d9a29dcdc3'},
            'quote': {'symbol': 'USD'}},
        # ONT / USD
        Address('0xfd7b3a77848f1c2d67e05e54d78d174a0c850335'):
        {'feed': {'address': '0x887f177cbed2cf555a64e7bf125e1825eb69db82'},
            'quote': {'symbol': 'USD'}},
        # PAXG / USD
        Address('0x7950865a9140cb519342433146ed5b40c6f210f7'):
        {'feed': {'address': '0x7f8cad4690a38ac28bda3d132ef83db1c17557df'},
            'quote': {'symbol': 'USD'}},
        # REEF / USD
        Address('0xf21768ccbc73ea5b6fd3c687208a7c2def2d966e'):
        {'feed': {'address': '0x46f13472a4d4fec9e07e8a00ee52f4fa77810736'},
            'quote': {'symbol': 'USD'}},
        # SHIB / USD
        Address('0x2859e4544c4bb03966803b044a93563bd2d0dd4d'):
        {'feed': {'address': '0xa615be6cb0f3f36a641858db6f30b9242d0abed8'},
            'quote': {'symbol': 'USD'}},
        # SXP / USD
        Address('0x47bead2563dcbf3bf2c9407fea4dc236faba485a'):
        {'feed': {'address': '0xe188a9875af525d25334d75f3327863b2b8cd0f1'},
            'quote': {'symbol': 'USD'}},
        # TRX / USD
        Address('0x85eac5ac2f758618dfa09bdbe0cf174e7d574d5b'):
        {'feed': {'address': '0xf4c5e535756d11994fcbb12ba8add0192d9b88be'},
            'quote': {'symbol': 'USD'}},
        # TUSD / USD
        Address('0x14016e85a25aeb13065688cafb43044c2ef86784'):
        {'feed': {'address': '0xa3334a9762090e827413a7495afece76f41dfc06'},
            'quote': {'symbol': 'USD'}},
        # TWT / BNB
        Address('0x4b0f1812e5df2a09796481ff14017e6005508003'):
        {'feed': {'address': '0x7e728dfa6bca9023d9abee759fdf56beab8ac7ad'},
            'quote': {'symbol': 'BNB'}},
        # UNI / USD
        Address('0xbf5140a22578168fd562dccf235e5d43a02ce9b1'):
        {'feed': {'address': '0xb57f259e7c24e56a1da00f66b55a5640d9f9e7e4'},
            'quote': {'symbol': 'USD'}},
        # USDC / USD
        Address('0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d'):
        {'feed': {'address': '0x51597f405303c4377e36123cbc172b13269ea163'},
            'quote': {'symbol': 'USD'}},
        # USDT / USD
        Address('0x55d398326f99059ff775485246999027b3197955'):
        {'feed': {'address': '0xb97ad0e74fa7d920791e90258a6e2085088b4320'},
            'quote': {'symbol': 'USD'}},
        # VAI / USD
        Address('0x4bd17003473389a42daf6a0a729f6fdb328bbbd7'):
        {'feed': {'address': '0x058316f8bb13acd442ee7a216c7b60cfb4ea1b53'},
            'quote': {'symbol': 'USD'}},
        # WIN / USD
        Address('0xaef0d72a118ce24fee3cd1d43d383897d05b4e99'):
        {'feed': {'address': '0x9e7377e194e41d63795907c92c3eb351a2eb0233'},
            'quote': {'symbol': 'USD'}},
        # XCN / USD
        Address('0x7324c7c0d95cebc73eea7e85cbaac0dbdf88a05b'):
        {'feed': {'address': '0x352757ff58aaf598e80fa4979cb7c60e2d32a13e'},
            'quote': {'symbol': 'USD'}},
        # XRP / USD
        Address('0x1d2f0da169ceb9fc7b3144628db156f3f6c60dbe'):
        {'feed': {'address': '0x93a67d414896a280bf8ffb3b389fe3686e014fda'},
            'quote': {'symbol': 'USD'}},
        # XTZ / USD
        Address('0x16939ef78684453bfdfb47825f8a5f714f12623a'):
        {'feed': {'address': '0x9a18137adcf7b05f033ad26968ed5a9cf0bf8e6b'},
            'quote': {'symbol': 'USD'}},
        # XVS / USD
        Address('0xcf6bb5389c92bdda8a3747ddb454cb7a64626c63'):
        {'feed': {'address': '0xbf63f430a79d4036a5900c19818aff1fa710f206'},
            'quote': {'symbol': 'USD'}},
        # YFI / USD
        Address('0x88f1a5ae2a3bf98aeaf342d26b30a79438c9142e'):
        {'feed': {'address': '0xd7eaa5bf3013a96e3d515c055dbd98dbdc8c620d'},
            'quote': {'symbol': 'USD'}},
        # YFII / USD
        Address('0x7f70642d88cf1c4a3a7abb072b53b929b653eda5'):
        {'feed': {'address': '0xc94580faaf145b2fd0ab5215031833c98d3b77e4'},
            'quote': {'symbol': 'USD'}},
        # ZIL / USD
        Address('0xb86abcb37c3a4b64f74f59301aff131a1becc787'):
        {'feed': {'address': '0x3e3aa4fc329529c8ab921c810850626021dba7e6'},
            'quote': {'symbol': 'USD'}}
    },
    Network.Polygon: {
        # 1INCH / USD
        Address('0x9c2c5fd7b07e95ee044ddeba0e97a665f142394f'):
        {'feed': {'address': '0x443c5116cdf663eb387e72c688d276e702135c87'},
            'quote': {'symbol': 'USD'}},
        # AAVE / USD
        Address('0xd6df932a45c0f255f85145f286ea0b292b21c90b'):
        {'feed': {'address': '0x72484b12719e23115761d5da1646945632979bb6'},
            'quote': {'symbol': 'USD'}},
        # ALPHA / USD
        Address('0x6a3e7c3c6ef65ee26975b12293ca1aad7e1daed2'):
        {'feed': {'address': '0x289833f252eab98582d62db94bd75ab48ad9cf0d'},
            'quote': {'symbol': 'USD'}},
        # APE / USD
        Address('0xb7b31a6bc18e48888545ce79e83e06003be70930'):
        {'feed': {'address': '0x2ac3f3bfac8fc9094bc3f0f9041a51375235b992'},
            'quote': {'symbol': 'USD'}},
        # AVAX / USD
        Address('0x2c89bbc92bd86f8075d1decc58c7f4e0107f286b'):
        {'feed': {'address': '0xe01ea2fbd8d76ee323fbed03eb9a8625ec981a10'},
            'quote': {'symbol': 'USD'}},
        # BAL / USD
        Address('0x9a71012b13ca4d3d0cdc72a177df3ef03b0e76a3'):
        {'feed': {'address': '0xd106b538f2a868c28ca1ec7e298c3325e0251d66'},
            'quote': {'symbol': 'USD'}},
        # BAT / USD
        Address('0x3cef98bb43d732e2f285ee605a8158cde967d219'):
        {'feed': {'address': '0x2346ce62bd732c62618944e51cbfa09d985d86d2'},
            'quote': {'symbol': 'USD'}},
        # BNB / USD
        Address('0x3ba4c387f786bfee076a58914f5bd38d668b42c3'):
        {'feed': {'address': '0x82a6c4af830caa6c97bb504425f6a66165c2c26e'},
            'quote': {'symbol': 'USD'}},
        # BNT / USD
        Address('0xc26d47d5c33ac71ac5cf9f776d63ba292a4f7842'):
        {'feed': {'address': '0xf5724884b6e99257cc003375e6b844bc776183f9'},
            'quote': {'symbol': 'USD'}},
        # BUSD / USD
        Address('0x9c9e5fd8bbc25984b178fdce6117defa39d2db39'):
        {'feed': {'address': '0xe0dc07d5ed74741ceeda61284ee56a2a0f7a4cc9'},
            'quote': {'symbol': 'USD'}},
        # CEL / USD
        Address('0xd85d1e945766fea5eda9103f918bd915fbca63e6'):
        {'feed': {'address': '0xc9ecf45956f576681bdc01f79602a79bc2667b0c'},
            'quote': {'symbol': 'USD'}},
        # CHZ / USD
        Address('0xf1938ce12400f9a761084e7a80d37e732a4da056'):
        {'feed': {'address': '0x2409987e514ad8b0973c2b90ee1d95051df0ecb9'},
            'quote': {'symbol': 'USD'}},
        # COMP / USD
        Address('0x8505b9d2254a7ae468c0e9dd10ccea3a837aef5c'):
        {'feed': {'address': '0x2a8758b7257102461bc958279054e372c2b1bde6'},
            'quote': {'symbol': 'USD'}},
        # CRV / USD
        Address('0x172370d5cd63279efa6d502dab29171933a610af'):
        {'feed': {'address': '0x336584c8e6dc19637a5b36206b1c79923111b405'},
            'quote': {'symbol': 'USD'}},
        # DAI / USD
        Address('0x8f3cf7ad23cd3cadbd9735aff958023239c6a063'):
        {'feed': {'address': '0x4746dec9e833a82ec7c2c1356372ccf2cfcd2f3d'},
            'quote': {'symbol': 'USD'}},
        # DPI / ETH
        Address('0x85955046df4668e1dd369d2de9f3aeb98dd2a369'):
        {'feed': {'address': '0xc70aaf9092de3a4e5000956e672cdf5e996b4610'},
            'quote': {'symbol': 'ETH'}},
        # ENJ / USD
        Address('0x7ec26842f195c852fa843bb9f6d8b583a274a157'):
        {'feed': {'address': '0x440a341bbc9fa86aa60a195e2409a547e48d4c0c'},
            'quote': {'symbol': 'USD'}},
        # FRAX / USD
        Address('0x45c32fa6df82ead1e2ef74d17b76547eddfaff89'):
        {'feed': {'address': '0x00dbeb1e45485d53df7c2f0df1aa0b6dc30311d3'},
            'quote': {'symbol': 'USD'}},
        # FTM / USD
        Address('0xc9c1c1c20b3658f8787cc2fd702267791f224ce1'):
        {'feed': {'address': '0x58326c0f831b2dbf7234a4204f28bba79aa06d5f'},
            'quote': {'symbol': 'USD'}},
        # FXS / USD
        Address('0x1a3acf6d19267e2d3e7f898f42803e90c9219062'):
        {'feed': {'address': '0x6c0fe985d3cacbcde428b84fc9431792694d0f51'},
            'quote': {'symbol': 'USD'}},
        # GHST / USD
        Address('0x385eeac5cb85a38a9a07a70c73e0a3271cfb54a7'):
        {'feed': {'address': '0xdd229ce42f11d8ee7fff29bdb71c7b81352e11be'},
            'quote': {'symbol': 'USD'}},
        # GNO / USD
        Address('0x5ffd62d3c3ee2e81c00a7b9079fb248e7df024a8'):
        {'feed': {'address': '0x432fa0899cf1bcdb98592d7eaa23c372b8b8ddf2'},
            'quote': {'symbol': 'USD'}},
        # GRT / USD
        Address('0x5fe2b58c013d7601147dcdd68c143a77499f5531'):
        {'feed': {'address': '0x3fabbfb300b1e2d7c9b84512fe9d30aedf24c410'},
            'quote': {'symbol': 'USD'}},
        # HT / USD
        Address('0xfad65eb62a97ff5ed91b23afd039956aaca6e93b'):
        {'feed': {'address': '0x6f8f9e75c0285aece30adfe1bcc1955f145d971a'},
            'quote': {'symbol': 'USD'}},
        # KEEP / USD
        Address('0x42f37a1296b2981f7c3caced84c5096b2eb0c72c'):
        {'feed': {'address': '0x5438e60a06c7447432512264fa57e2fed3224b33'},
            'quote': {'symbol': 'USD'}},
        # KNC / USD
        Address('0x1c954e8fe737f99f68fa1ccda3e51ebdb291948c'):
        {'feed': {'address': '0x10e5f3dfc81b3e5ef4e648c4454d04e79e1e41e2'},
            'quote': {'symbol': 'USD'}},
        # LINK / USD
        Address('0xb0897686c545045afc77cf20ec7a532e3120e0f1'):
        {'feed': {'address': '0xd9ffdb71ebe7496cc440152d43986aae0ab76665'},
            'quote': {'symbol': 'USD'}},
        # LPT / USD
        Address('0x3962f4a0a0051dcce0be73a7e09cef5756736712'):
        {'feed': {'address': '0xbaaf11ceda1d1ca9cf01748f8196653c9656a400'},
            'quote': {'symbol': 'USD'}},
        # MANA / USD
        Address('0xa1c57f48f0deb89f569dfbe6e2b7f46d33606fd4'):
        {'feed': {'address': '0xa1cbf3fe43bc3501e3fc4b573e822c70e76a7512'},
            'quote': {'symbol': 'USD'}},
        # MATIC / USD
        Address('0x0000000000000000000000000000000000001010'):
        {'feed': {'address': '0xab594600376ec9fd91f8e885dadf0ce036862de0'},
            'quote': {'symbol': 'USD'}},
        # MFT / USD
        Address('0x91ca694d2b293f70fe722fba7d8a5259188959c3'):
        {'feed': {'address': '0x6e53c1c22427258be55ae985a65c0c87bb631f9c'},
            'quote': {'symbol': 'USD'}},
        # MIMATIC / USD
        Address('0xa3fa99a148fa48d14ed51d610c367c61876997f1'):
        {'feed': {'address': '0xd8d483d813547cfb624b8dc33a00f2fcbcd2d428'},
            'quote': {'symbol': 'USD'}},
        # MKR / USD
        Address('0x6f7c932e7684666c9fd1d44527765433e01ff61d'):
        {'feed': {'address': '0xa070427bf5ba5709f70e98b94cb2f435a242c46c'},
            'quote': {'symbol': 'USD'}},
        # NEXO / USD
        Address('0x41b3966b4ff7b427969ddf5da3627d6aeae9a48e'):
        {'feed': {'address': '0x666bb13b3ed3816504e8c30d0f9b9c16b371774b'},
            'quote': {'symbol': 'USD'}},
        # OGN / USD
        Address('0xa63beffd33ab3a2efd92a39a7d2361cee14ceba8'):
        {'feed': {'address': '0x8ec0ec2e0f26d8253abf39db4b1793d76b49c6d5'},
            'quote': {'symbol': 'USD'}},
        # OM / USD
        Address('0xc3ec80343d2bae2f8e680fdadde7c17e71e114ea'):
        {'feed': {'address': '0xc86105dccf9bd629cea7fd41f94c6050bf96d57f'},
            'quote': {'symbol': 'USD'}},
        # OMG / USD
        Address('0x62414d03084eeb269e18c970a21f45d2967f0170'):
        {'feed': {'address': '0x93ffee768f74208a7b9f2a4426f0f6bcbb1d09de'},
            'quote': {'symbol': 'USD'}},
        # PAX / USD
        Address('0x6f3b3286fd86d8b47ec737ceb3d0d354cc657b3e'):
        {'feed': {'address': '0x56d55d34ecc616e71ae998accba79f236ff2ff46'},
            'quote': {'symbol': 'USD'}},
        # PAXG / USD
        Address('0x553d3d295e0f695b9228246232edf400ed3560b5'):
        {'feed': {'address': '0x0f6914d8e7e1214cdb3a4c6fbf729b75c69df608'},
            'quote': {'symbol': 'USD'}},
        # POLY / USD
        Address('0xcb059c5573646047d6d88dddb87b745c18161d3b'):
        {'feed': {'address': '0xc741f7752bae936fce97933b755884af66fb69c1'},
            'quote': {'symbol': 'USD'}},
        # QUICK / USD
        Address('0xb5c064f955d8e7f38fe0460c556a72987494ee17'):
        {'feed': {'address': '0xa058689f4bca95208bba3f265674ae95ded75b6d'},
            'quote': {'symbol': 'USD'}},
        # SAND / USD
        Address('0xbbba073c31bf03b8acf7c28ef0738decf3695683'):
        {'feed': {'address': '0x3d49406edd4d52fb7ffd25485f32e073b529c924'},
            'quote': {'symbol': 'USD'}},
        # SNX / USD
        Address('0x50b728d8d964fd00c2d0aad81718b71311fef68a'):
        {'feed': {'address': '0xbf90a5d9b6ee9019028dbfc2a9e50056d5252894'},
            'quote': {'symbol': 'USD'}},
        # SRM / USD
        Address('0x6bf2eb299e51fc5df30dec81d9445dde70e3f185'):
        {'feed': {'address': '0xd8f8a7a38a1ac326312000d0a0218bf3216bfabb'},
            'quote': {'symbol': 'USD'}},
        # SUSHI / USD
        Address('0x0b3f868e0be5597d5db7feb59e1cadbb0fdda50a'):
        {'feed': {'address': '0x49b0c695039243bbfeb8ecd054eb70061fd54aa0'},
            'quote': {'symbol': 'USD'}},
        # THETA / USD
        Address('0xb46e0ae620efd98516f49bb00263317096c114b2'):
        {'feed': {'address': '0x38611b09f8f2d520c14ea973765c225bf57b9eac'},
            'quote': {'symbol': 'USD'}},
        # TRY / USD
        Address('0xefee2de82343be622dcb4e545f75a3b9f50c272d'):
        {'feed': {'address': '0xd78325dca0f90f0ffe53ccea1b02bb12e1bf8fdb'},
            'quote': {'symbol': 'USD'}},
        # TUSD / USD
        Address('0x2e1ad108ff1d8c782fcbbb89aad783ac49586756'):
        {'feed': {'address': '0x7c5d415b64312d38c56b54358449d0a4058339d2'},
            'quote': {'symbol': 'USD'}},
        # UMA / USD
        Address('0x3066818837c5e6ed6601bd5a91b0762877a6b731'):
        {'feed': {'address': '0x33d9b1baadcf4b26ab6f8e83e9cb8a611b2b3956'},
            'quote': {'symbol': 'USD'}},
        # UNI / USD
        Address('0xb33eaad8d922b1083446dc23f610c2567fb5180f'):
        {'feed': {'address': '0xdf0fb4e4f928d2dcb76f438575fdd8682386e13c'},
            'quote': {'symbol': 'USD'}},
        # USDC / USD
        Address('0x2791bca1f2de4661ed88a30c99a7a9449aa84174'):
        {'feed': {'address': '0xfe4a8cc5b5b2366c1b58bea3858e81843581b2f7'},
            'quote': {'symbol': 'USD'}},
        # USDT / USD
        Address('0xc2132d05d31c914a87c6611c10748aeb04b58e8f'):
        {'feed': {'address': '0x0a6513e40db6eb1b165753ad52e80663aea50545'},
            'quote': {'symbol': 'USD'}},
        # WBTC / USD
        Address('0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6'):
        {'feed': {'address': '0xde31f8bfbd8c84b5360cfacca3539b938dd78ae6'},
            'quote': {'symbol': 'USD'}},
        # WOO / USD
        Address('0x1b815d120b3ef02039ee11dc2d33de7aa4a8c603'):
        {'feed': {'address': '0x6a99ec84819fb7007dd5d032068742604e755c56'},
            'quote': {'symbol': 'USD'}},
        # YFI / USD
        Address('0xda537104d6a5edd53c6fbba9a898708e465260b6'):
        {'feed': {'address': '0x9d3a43c111e7b2c6601705d9fcf7a70c95b1dc55'},
            'quote': {'symbol': 'USD'}},
        # ZEC: using BSC's contract address
        Address('0x1ba42e5193dfa8b03d15dd1b86a3113bbbef8eeb'):
        {'feed': {'address': '0x6EA4d89474d9410939d429B786208c74853A5B47'},
            'quote': {'symbol': 'USD'}},
        # ZRX / USD
        Address('0x5559edb74751a0ede9dea4dc23aee72cca6be3d5'):
        {'feed': {'address': '0x6ea4d89474d9410939d429b786208c74853a5b47'},
            'quote': {'symbol': 'USD'}}
    },
    Network.ArbitrumOne: {
        # AAVE / USD
        Address('0xba5ddd1f9d7f570dc94a51479a000e3bce967196'):
        {'feed': {'address': '0x3c6AbdA21358c15601A3175D8dd66D0c572cc904'},
            'quote': {'symbol': 'USD'}},
        # APE / USD
        Address('0x74885b4d524d497261259b38900f54e6dbad2210'):
        {'feed': {'address': '0x076577765a3e66db410eCc1372d0B0dB503A42C5'},
            'quote': {'symbol': 'USD'}},
        # AXS / USD
        Address('0xe88998fb579266628af6a03e3821d5983e5d0089'):
        {'feed': {'address': '0xA303a72d334e589122454e8e849E147BAd309E73'},
            'quote': {'symbol': 'USD'}},
        # BAL / USD
        Address('0x040d1edc9569d4bab2d15287dc5a4f10f56a56b8'):
        {'feed': {'address': '0x53368bC6a7eB4f4AF3d6974520FEba0295A5daAb'},
            'quote': {'symbol': 'USD'}},
        # BTC / USD
        Address('0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'):
        {'feed': {'address': '0x942d00008D658dbB40745BBEc89A93c253f9B882'},
            'quote': {'symbol': 'USD'}},
        # BUSD / USD
        Address('0x31190254504622cefdfa55a7d3d272e6462629a2'):
        {'feed': {'address': '0x6c77960BEB512D955cCe2d5eaA1Ea20A388Ba9a2'},
            'quote': {'symbol': 'USD'}},
        # COMP / USD
        Address('0x354a6da3fcde098f8389cad84b0182725c6c91de'):
        {'feed': {'address': '0x52df0481c6D2Ad7E50889AFd03C8ddd8413ac63d'},
            'quote': {'symbol': 'USD'}},
        # CRV / USD
        Address('0x11cdb42b0eb46d95f990bedd4695a6e3fa034978'):
        {'feed': {'address': '0x79DaA21a44D1415306Ec17C361e0090bdD4cFCbe'},
            'quote': {'symbol': 'USD'}},
        # CVX / USD
        Address('0xaafcfd42c9954c6689ef1901e03db742520829c5'):
        {'feed': {'address': '0x3d62E33E97de1F0ce913dB62d5972722C2A7E4f6'},
            'quote': {'symbol': 'USD'}},
        # DAI / USD
        Address('0xda10009cbd5d07dd0cecc66161fc93d7c9000da1'):
        {'feed': {'address': '0xFc06bB03a9e1D8033f87eA6A682cbd65477A43b9'},
            'quote': {'symbol': 'USD'}},
        # DODO / USD
        Address('0x69eb4fa4a2fbd498c257c57ea8b7655a2559a581'):
        {'feed': {'address': '0xc195bA27455182e3Bb6F86dAB5838901604Ba72c'},
            'quote': {'symbol': 'USD'}},
        # DPX / USD
        Address('0x6c2c06790b3e3e3c38e12ee22f8183b37a13ee55'):
        {'feed': {'address': '0x2489462e64Ea205386b7b8737609B3701047a77d'},
            'quote': {'symbol': 'USD'}},
        # ETH / USD
        Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
        {'feed': {'address': '0x3607e46698d218B3a5Cae44bF381475C0a5e2ca7'},
            'quote': {'symbol': 'USD'}},
        # FEI / USD
        Address('0x4a717522566c7a09fd2774ccedc5a8c43c5f9fd2'):
        {'feed': {'address': '0xbd3BB32A3fd843B066AB29Ae42C63D44028E20D8'},
            'quote': {'symbol': 'USD'}},
        # FRAX / USD
        Address('0x17fc002b466eec40dae837fc4be5c67993ddbd6f'):
        {'feed': {'address': '0x5D041081725468Aa43e72ff0445Fde2Ad1aDE775'},
            'quote': {'symbol': 'USD'}},
        # FXS / USD
        Address('0x9d2f299715d94d8a7e6f5eaa8e654e8c74a988a7'):
        {'feed': {'address': '0xf8C6DE435CF8d06897a4A66b21df623D06d2A761'},
            'quote': {'symbol': 'USD'}},
        # GMX / USD
        Address('0xfc5a1a6eb076a2c7ad06ed22c90d7e710e35ad0a'):
        {'feed': {'address': '0xF6328F007A2FDc547875e24A3BC7e0603fd01727'},
            'quote': {'symbol': 'USD'}},
        # KNC / USD
        Address('0xe4dddfe67e7164b0fe14e218d80dc4c08edc01cb'):
        {'feed': {'address': '0x20870D99455B6F9d7c0E6f2608245719d789ff53'},
            'quote': {'symbol': 'USD'}},
        # LINK / ETH
        Address('0xf97f4df75117a78c1a5a0dbb814af92458539fb4'):
        {'feed': {'address': '0xa136978a2c8a92ec5EacC5179642AA2E1c1Eae18'},
            'quote': {'symbol': 'ETH'}},
        # MAGIC / USD
        Address('0x539bde0d7dbd336b79148aa742883198bbf60342'):
        {'feed': {'address': '0x5ab0B1e2604d4B708721bc3cD1ce962958b4297E'},
            'quote': {'symbol': 'USD'}},
        # MATIC / USD
        Address('0x561877b6b3dd7651313794e5f2894b2f18be0766'):
        {'feed': {'address': '0xA4A2b2000d447CC1086d15C077730008b0251FFD'},
            'quote': {'symbol': 'USD'}},
        # MIM / USD
        Address('0xfea7a6a0b346362bf88a9e4a88416b77a57d6c2a'):
        {'feed': {'address': '0x0Ae17556F9698fC47C365A746AB9CddCB17F3809'},
            'quote': {'symbol': 'USD'}},
        # PAXG / USD
        Address('0xfeb4dfc8c4cf7ed305bb08065d08ec6ee6728429'):
        {'feed': {'address': '0x2e4c363449E2EC7E93cd9ed4F3843c2CA4497108'},
            'quote': {'symbol': 'USD'}},
        # SOL / USD
        Address('0xb74da9fe2f96b9e0a5f4a3cf0b92dd2bec617124'):
        {'feed': {'address': '0x8C4308F7cbD7fB829645853cD188500D7dA8610a'},
            'quote': {'symbol': 'USD'}},
        # SPELL / USD
        Address('0x3e6648c5a70a150a88bce65f4ad4d506fe15d2af'):
        {'feed': {'address': '0xf6bACC7750c23A34b996A355A6E78b17Fc4BaEdC'},
            'quote': {'symbol': 'USD'}},
        # SUSHI / USD
        Address('0xd4d42f0b6def4ce0383636770ef773390d85c61a'):
        {'feed': {'address': '0xe4A492420eBdA03B04973Ed1E46d5fe9F3b077EF'},
            'quote': {'symbol': 'USD'}},
        # UNI / USD
        Address('0xfa7f8980b0f1e64a2062791cc3b0871572f1f7f0'):
        {'feed': {'address': '0xeFc5061B7a8AeF31F789F1bA5b3b8256674F2B71'},
            'quote': {'symbol': 'USD'}},
        # USDC / USD
        Address('0xff970a61a04b1ca14834a43f5de4533ebddb5cc8'):
        {'feed': {'address': '0x2946220288DbBF77dF0030fCecc2a8348CbBE32C'},
            'quote': {'symbol': 'USD'}},
        # USDD / USD
        Address('0x680447595e8b7b3aa1b43beb9f6098c79ac2ab3f'):
        {'feed': {'address': '0xd9fCb26FE3D4589c3e2ecD6A2A3af54EdDB67240'},
            'quote': {'symbol': 'USD'}},
        # USDT / USD
        Address('0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9'):
        {'feed': {'address': '0xCb35fE6E53e71b30301Ec4a3948Da4Ad3c65ACe4'},
            'quote': {'symbol': 'USD'}},
        # WBTC / USD
        Address('0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f'):
        {'feed': {'address': '0xb20bd22d3D2E5a628523d37b3DED569598EB649b'},
            'quote': {'symbol': 'USD'}},
        # YFI / USD
        Address('0x82e3a8f066a6989666b031d916c43672085b1582'):
        {'feed': {'address': '0x660e7aF290F540205A84dccC1F40D0269fC936F5'},
            'quote': {'symbol': 'USD'}}
    },
    Network.Optimism: {
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
    },
}
