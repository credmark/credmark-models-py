from credmark.cmf.types import Address

CHAINLINK_OVERRIDE_FEED_BSC = {
    # 1INCH / USD
    Address('0x111111111117dc0aa78b770fa6a738034120c302'):
    {'feed': {'address': '0x9a177Bb9f5b6083E962f9e62bD21d4b5660Aeb03'},
        'quote': {'symbol': 'USD'}},
    # AAVE / USD
    Address('0xfb6115445bff7b52feb98650c87f44907e58f802'):
    {'feed': {'address': '0xA8357BF572460fC40f4B0aCacbB2a6A61c89f475'},
        'quote': {'symbol': 'USD'}},
    # ADA / BNB
    Address('0x3ee2200efb3400fabb9aacf31297cbdd1d435d47'):
    {'feed': {'address': '0x2d5Fc41d1365fFe13d03d91E82e04Ca878D69f4B'},
        'quote': {'symbol': 'BNB'}},
    # ADA / USD
    Address('0x3ee2200efb3400fabb9aacf31297cbdd1d435d47'):
    {'feed': {'address': '0xa767f745331D267c7751297D982b050c93985627'},
        'quote': {'symbol': 'USD'}},
    # ALPACA / USD
    Address('0x8f0528ce5ef7b51152a59745befdd91d97091d2f'):
    {'feed': {'address': '0xe0073b60833249ffd1bb2af809112c2fbf221DF6'},
        'quote': {'symbol': 'USD'}},
    # ALPHA / BNB
    Address('0xa1faa113cbe53436df28ff0aee54275c13b40975'):
    {'feed': {'address': '0x7bC032A7C19B1BdCb981D892854d090cfB0f238E'},
        'quote': {'symbol': 'BNB'}},
    # ARPA / USD
    Address('0x6f769e65c14ebd1f68817f5f1dcdb61cfa2d6f7e'):
    {'feed': {'address': '0x31E0110f8c1376a699C8e3E65b5110e0525A811d'},
        'quote': {'symbol': 'USD'}},
    # ATOM / USD
    Address('0x0eb3a705fc54725037cc9e008bdede697f62f335'):
    {'feed': {'address': '0xb056B7C804297279A9a673289264c17E6Dc6055d'},
        'quote': {'symbol': 'USD'}},
    # AUTO / USD
    Address('0xa184088a740c695e156f91f5cc086a06bb78b827'):
    {'feed': {'address': '0x88E71E6520E5aC75f5338F5F0c9DeD9d4f692cDA'},
        'quote': {'symbol': 'USD'}},
    # AVAX / USD
    Address('0x1ce0c2827e2ef14d5c4f29a091d735a204794041'):
    {'feed': {'address': '0x5974855ce31EE8E1fff2e76591CbF83D7110F151'},
        'quote': {'symbol': 'USD'}},
    # AXS / USD
    Address('0x715d400f88c167884bbcc41c5fea407ed4d2f8a0'):
    {'feed': {'address': '0x7B49524ee5740c99435f52d731dFC94082fE61Ab'},
        'quote': {'symbol': 'USD'}},
    # BAND / BNB
    Address('0xad6caeb32cd2c308980a548bd0bc5aa4306c6c18'):
    {'feed': {'address': '0x3334bF7ec892Ca03D1378B51769b7782EAF318C4'},
        'quote': {'symbol': 'BNB'}},
    # BAND / USD
    Address('0xad6caeb32cd2c308980a548bd0bc5aa4306c6c18'):
    {'feed': {'address': '0xC78b99Ae87fF43535b0C782128DB3cB49c74A4d3'},
        'quote': {'symbol': 'USD'}},
    # BCH / BNB
    Address('0x8ff795a6f4d97e7887c79bea79aba5cc76444adf'):
    {'feed': {'address': '0x2a548935a323Bb7329a5E3F1667B979f16Bc890b'},
        'quote': {'symbol': 'BNB'}},
    # BCH / USD
    Address('0x8ff795a6f4d97e7887c79bea79aba5cc76444adf'):
    {'feed': {'address': '0x43d80f616DAf0b0B42a928EeD32147dC59027D41'},
        'quote': {'symbol': 'USD'}},
    # BETH / USD
    Address('0x250632378e573c6be1ac2f97fcdf00515d0aa91b'):
    {'feed': {'address': '0x2A3796273d47c4eD363b361D3AEFb7F7E2A13782'},
        'quote': {'symbol': 'USD'}},
    # BIFI / BNB
    Address('0xca3f508b8e4dd382ee878a314789373d80a5190a'):
    {'feed': {'address': '0xE6A9106Fca5d6552f3f1a3B3B33b62eb2F6F5347'},
        'quote': {'symbol': 'BNB'}},
    # BIFI / USD
    Address('0xca3f508b8e4dd382ee878a314789373d80a5190a'):
    {'feed': {'address': '0xaB827b69daCd586A37E80A7d552a4395d576e645'},
        'quote': {'symbol': 'USD'}},
    # BNB / USD
    Address('0x0000000000000000010000100100111001000010'):
    {'feed': {'address': '0x0567F2323251f0Aab15c8dFb1967E4e8A7D42aeE'},
        'quote': {'symbol': 'USD'}},
    # BORING / BNB
    Address('0xffeecbf8d7267757c2dc3d13d730e97e15bfdf7f'):
    {'feed': {'address': '0xeAC5322C6b841FE1466D42D9Cfa1cE75c51d6ae3'},
        'quote': {'symbol': 'BNB'}},
    # BSW / USD
    Address('0x965f527d9159dce6288a2219db51fc6eef120dd1'):
    {'feed': {'address': '0x08E70777b982a58D23D05E3D7714f44837c06A21'},
        'quote': {'symbol': 'USD'}},
    # BTC / BNB
    Address('0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'):
    {'feed': {'address': '0x116EeB23384451C78ed366D4f67D5AD44eE771A0'},
        'quote': {'symbol': 'BNB'}},
    # BTC / ETH
    Address('0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'):
    {'feed': {'address': '0xf1769eB4D1943AF02ab1096D7893759F6177D6B8'},
        'quote': {'symbol': 'ETH'}},
    # BTC / USD
    Address('0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'):
    {'feed': {'address': '0x264990fbd0A4796A3E3d8E37C4d5F87a3aCa5Ebf'},
        'quote': {'symbol': 'USD'}},
    # BUSD / BNB
    Address('0xe9e7cea3dedca5984780bafc599bd69add087d56'):
    {'feed': {'address': '0x87Ea38c9F24264Ec1Fff41B04ec94a97Caf99941'},
        'quote': {'symbol': 'BNB'}},
    # BUSD / USD
    Address('0xe9e7cea3dedca5984780bafc599bd69add087d56'):
    {'feed': {'address': '0xcBb98864Ef56E9042e7d2efef76141f15731B82f'},
        'quote': {'symbol': 'USD'}},
    # C98 / USD
    Address('0xaec945e04baf28b135fa7c640f624f8d90f1c3a6'):
    {'feed': {'address': '0x889158E39628C0397DC54B84F6b1cbe0AaEb7FFc'},
        'quote': {'symbol': 'USD'}},
    # CAKE / BNB
    Address('0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82'):
    {'feed': {'address': '0xcB23da9EA243f53194CBc2380A6d4d9bC046161f'},
        'quote': {'symbol': 'BNB'}},
    # CAKE / USD
    Address('0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82'):
    {'feed': {'address': '0xB6064eD41d4f67e353768aA239cA86f4F73665a1'},
        'quote': {'symbol': 'USD'}},
    # CHR / USD
    Address('0xf9cec8d50f6c8ad3fb6dccec577e05aa32b224fe'):
    {'feed': {'address': '0x1f771B2b1F3c3Db6C7A1d5F38961a49CEcD116dA'},
        'quote': {'symbol': 'USD'}},
    # COMP / USD
    Address('0x52ce071bd9b1c4b00a0b92d298c512478cad67e8'):
    {'feed': {'address': '0x0Db8945f9aEf5651fa5bd52314C5aAe78DfDe540'},
        'quote': {'symbol': 'USD'}},
    # CREAM / BNB
    Address('0xd4cb328a82bdf5f03eb737f37fa6b370aef3e888'):
    {'feed': {'address': '0x6f55DFAf098a813d87BB4e6392275b502360Bb9D'},
        'quote': {'symbol': 'BNB'}},
    # DAI / BNB
    Address('0x1af3f329e8be154074d8769d1ffa4ee058b1dbc3'):
    {'feed': {'address': '0x8EC213E7191488C7873cEC6daC8e97cdbAdb7B35'},
        'quote': {'symbol': 'BNB'}},
    # DAI / USD
    Address('0x1af3f329e8be154074d8769d1ffa4ee058b1dbc3'):
    {'feed': {'address': '0x132d3C0B1D2cEa0BC552588063bdBb210FDeecfA'},
        'quote': {'symbol': 'USD'}},
    # DF / USD
    Address('0x4a9a2b2b04549c3927dd2c9668a5ef3fca473623'):
    {'feed': {'address': '0x1b816F5E122eFa230300126F97C018716c4e47F5'},
        'quote': {'symbol': 'USD'}},
    # DODO / BNB
    Address('0x67ee3cb086f8a16f34bee3ca72fad36f7db929e2'):
    {'feed': {'address': '0x120ae15CB86060527BFD431Abd3FF51890D2032C'},
        'quote': {'symbol': 'BNB'}},
    # DODO / USD
    Address('0x67ee3cb086f8a16f34bee3ca72fad36f7db929e2'):
    {'feed': {'address': '0x87701B15C08687341c2a847ca44eCfBc8d7873E1'},
        'quote': {'symbol': 'USD'}},
    # DOGE / USD
    Address('0xba2ae424d960c26247dd6c32edc70b295c744c43'):
    {'feed': {'address': '0x3AB0A0d137D4F946fBB19eecc6e92E64660231C8'},
        'quote': {'symbol': 'USD'}},
    # DOT / BNB
    Address('0x7083609fce4d1d8dc0c979aab8c869ea2c873402'):
    {'feed': {'address': '0xBA8683E9c3B1455bE6e18E7768e8cAD95Eb5eD49'},
        'quote': {'symbol': 'BNB'}},
    # DOT / USD
    Address('0x7083609fce4d1d8dc0c979aab8c869ea2c873402'):
    {'feed': {'address': '0xC333eb0086309a16aa7c8308DfD32c8BBA0a2592'},
        'quote': {'symbol': 'USD'}},
    # EOS / BNB
    Address('0x56b6fb708fc5732dec1afc8d8556423a2edccbd6'):
    {'feed': {'address': '0xed93F3764334788f2f6628b30e505fe1fc5d1D7b'},
        'quote': {'symbol': 'BNB'}},
    # EOS / USD
    Address('0x56b6fb708fc5732dec1afc8d8556423a2edccbd6'):
    {'feed': {'address': '0xd5508c8Ffdb8F15cE336e629fD4ca9AdB48f50F0'},
        'quote': {'symbol': 'USD'}},
    # ETH / BNB
    Address('0x2170ed0880ac9a755fd29b2688956bd959f933f8'):
    {'feed': {'address': '0x63D407F32Aa72E63C7209ce1c2F5dA40b3AaE726'},
        'quote': {'symbol': 'BNB'}},
    # ETH / USD
    Address('0x2170ed0880ac9a755fd29b2688956bd959f933f8'):
    {'feed': {'address': '0x9ef1B8c0E4F7dc8bF5719Ea496883DC6401d5b2e'},
        'quote': {'symbol': 'USD'}},
    # FET / USD
    Address('0x031b41e504677879370e9dbcf937283a8691fa7f'):
    {'feed': {'address': '0x657e700c66C48c135c4A29c4292908DbdA7aa280'},
        'quote': {'symbol': 'USD'}},
    # FIL / USD
    Address('0x0d8ce2a99bb6e3b7db580ed848240e4a0f9ae153'):
    {'feed': {'address': '0xE5dbFD9003bFf9dF5feB2f4F445Ca00fb121fb83'},
        'quote': {'symbol': 'USD'}},
    # FRAX / USD
    Address('0x90c97f71e18723b0cf0dfa30ee176ab653e89f40'):
    {'feed': {'address': '0x13A9c98b07F098c5319f4FF786eB16E22DC738e1'},
        'quote': {'symbol': 'USD'}},
    # FTM / USD
    Address('0xad29abb318791d579433d831ed122afeaf29dcfe'):
    {'feed': {'address': '0xe2A47e87C0f4134c8D06A41975F6860468b2F925'},
        'quote': {'symbol': 'USD'}},
    # FXS / USD
    Address('0xe48a3d7d0bc88d552f730b62c006bc925eadb9ee'):
    {'feed': {'address': '0x0E9D55932893Fb1308882C7857285B2B0bcc4f4a'},
        'quote': {'symbol': 'USD'}},
    # GMT / USD
    Address('0x3019bf2a2ef8040c242c9a4c5c4bd4c81678b2a1'):
    {'feed': {'address': '0x8b0D36ae4CF8e277773A7ba5F35c09Edb144241b'},
        'quote': {'symbol': 'USD'}},
    # HIGH / USD
    Address('0x5f4bde007dc06b867f86ebfe4802e34a1ffeed63'):
    {'feed': {'address': '0xdF4Dd957a84F798acFADd448badd2D8b9bC99047'},
        'quote': {'symbol': 'USD'}},
    # INJ / USD
    Address('0xa2b726b1145a4773f68593cf171187d8ebe4d495'):
    {'feed': {'address': '0x63A9133cd7c611d6049761038C16f238FddA71d7'},
        'quote': {'symbol': 'USD'}},
    # KAVA / USD
    Address('0x5f88ab06e8dfe89df127b2430bba4af600866035'):
    {'feed': {'address': '0x12bf0C3f7D5aca9E711930d704dA2774358d9210'},
        'quote': {'symbol': 'USD'}},
    # KNC / USD
    Address('0xfe56d5892bdffc7bf58f2e84be1b2c32d21c308b'):
    {'feed': {'address': '0xF2f8273F6b9Fc22C90891DC802cAf60eeF805cDF'},
        'quote': {'symbol': 'USD'}},
    # LINA / USD
    Address('0x762539b45a1dcce3d36d080f74d1aed37844b878'):
    {'feed': {'address': '0x38393201952f2764E04B290af9df427217D56B41'},
        'quote': {'symbol': 'USD'}},
    # LINK / BNB
    Address('0xf8a0bf9cf54bb92f17374d9e9a321e6a111a51bd'):
    {'feed': {'address': '0xB38722F6A608646a538E882Ee9972D15c86Fc597'},
        'quote': {'symbol': 'BNB'}},
    # LINK / USD
    Address('0xf8a0bf9cf54bb92f17374d9e9a321e6a111a51bd'):
    {'feed': {'address': '0xca236E327F629f9Fc2c30A4E95775EbF0B89fac8'},
        'quote': {'symbol': 'USD'}},
    # LIT / USD
    Address('0xb59490ab09a0f526cc7305822ac65f2ab12f9723'):
    {'feed': {'address': '0x83766bA8d964fEAeD3819b145a69c947Df9Cb035'},
        'quote': {'symbol': 'USD'}},
    # LTC / BNB
    Address('0x4338665cbb7b2485a8855a139b75d5e34ab0db94'):
    {'feed': {'address': '0x4e5a43A79f53c0a8e83489648Ea7e429278f8b2D'},
        'quote': {'symbol': 'BNB'}},
    # LTC / USD
    Address('0x4338665cbb7b2485a8855a139b75d5e34ab0db94'):
    {'feed': {'address': '0x74E72F37A8c415c8f1a98Ed42E78Ff997435791D'},
        'quote': {'symbol': 'USD'}},
    # MASK / USD
    Address('0x2ed9a5c8c13b93955103b9a7c167b67ef4d568a3'):
    {'feed': {'address': '0x4978c0abE6899178c1A74838Ee0062280888E2Cf'},
        'quote': {'symbol': 'USD'}},
    # MATIC / USD
    Address('0xcc42724c6683b7e57334c4e856f4c9965ed682bd'):
    {'feed': {'address': '0x7CA57b0cA6367191c94C8914d7Df09A57655905f'},
        'quote': {'symbol': 'USD'}},
    # MBOX / USD
    Address('0x3203c9e46ca618c8c1ce5dc67e7e9d75f5da2377'):
    {'feed': {'address': '0x1AAE42AA46483370Be23274Abb29Bcc40f808a4c'},
        'quote': {'symbol': 'USD'}},
    # MDX / USD
    Address('0x9c65ab58d8d978db963e63f2bfb7121627e3a739'):
    {'feed': {'address': '0x9165366bf450a6906D25549f0E0f8E6586Fc93E2'},
        'quote': {'symbol': 'USD'}},
    # MIM / USD
    Address('0xfe19f0b51438fd612f6fd59c1dbb3ea319f433ba'):
    {'feed': {'address': '0xc9D267542B23B41fB93397a93e5a1D7B80Ea5A01'},
        'quote': {'symbol': 'USD'}},
    # NEAR / USD
    Address('0x1fa4a73a3f0133f0025378af00236f3abdee5d63'):
    {'feed': {'address': '0x0Fe4D87883005fCAFaF56B81d09473D9A29dCDC3'},
        'quote': {'symbol': 'USD'}},
    # NULS / USD
    Address('0x8cd6e29d3686d24d3c2018cee54621ea0f89313b'):
    {'feed': {'address': '0xaCFBE73231d312AC6954496b3f786E892bF0f7e5'},
        'quote': {'symbol': 'USD'}},
    # ONG / USD
    Address('0x308bfaeaac8bdab6e9fc5ead8edcb5f95b0599d9'):
    {'feed': {'address': '0xcF95796f3016801A1dA5C518Fc7A59C51dcEf793'},
        'quote': {'symbol': 'USD'}},
    # ONT / USD
    Address('0xfd7b3a77848f1c2d67e05e54d78d174a0c850335'):
    {'feed': {'address': '0x887f177CBED2cf555a64e7bF125E1825EB69dB82'},
        'quote': {'symbol': 'USD'}},
    # PAXG / USD
    Address('0x7950865a9140cb519342433146ed5b40c6f210f7'):
    {'feed': {'address': '0x7F8caD4690A38aC28BDA3D132eF83DB1C17557Df'},
        'quote': {'symbol': 'USD'}},
    # RDNT / USD
    Address('0xf7de7e8a6bd59ed41a4b5fe50278b3b7f31384df'):
    {'feed': {'address': '0x20123C6ebd45c6496102BeEA86e1a6616Ca547c6'},
        'quote': {'symbol': 'USD'}},
    # REEF / USD
    Address('0xf21768ccbc73ea5b6fd3c687208a7c2def2d966e'):
    {'feed': {'address': '0x46f13472A4d4FeC9E07E8A00eE52f4Fa77810736'},
        'quote': {'symbol': 'USD'}},
    # SHIB / USD
    Address('0x2859e4544c4bb03966803b044a93563bd2d0dd4d'):
    {'feed': {'address': '0xA615Be6cb0f3F36A641858dB6F30B9242d0ABeD8'},
        'quote': {'symbol': 'USD'}},
    # SOL / USD
    Address('0x570a5d26f7765ecb712c0924e4de545b89fd43df'):
    {'feed': {'address': '0x0E8a53DD9c13589df6382F13dA6B3Ec8F919B323'},
        'quote': {'symbol': 'USD'}},
    # SPELL / USD
    Address('0x9fe28d11ce29e340b7124c493f59607cbab9ce48'):
    {'feed': {'address': '0x47e01580C537Cd47dA339eA3a4aFb5998CCf037C'},
        'quote': {'symbol': 'USD'}},
    # SUSHI / USD
    Address('0x947950bcc74888a40ffa2593c5798f11fc9124c4'):
    {'feed': {'address': '0xa679C72a97B654CFfF58aB704de3BA15Cde89B07'},
        'quote': {'symbol': 'USD'}},
    # SXP / USD
    Address('0x47bead2563dcbf3bf2c9407fea4dc236faba485a'):
    {'feed': {'address': '0xE188A9875af525d25334d75F3327863B2b8cd0F1'},
        'quote': {'symbol': 'USD'}},
    # TRX / USD
    Address('0xce7de646e7208a4ef112cb6ed5038fa6cc6b12e3'):
    {'feed': {'address': '0xF4C5e535756D11994fCBB12Ba8adD0192D9b88be'},
        'quote': {'symbol': 'USD'}},
    # TUSD / USD
    Address('0x14016e85a25aeb13065688cafb43044c2ef86784'):
    {'feed': {'address': '0xa3334A9762090E827413A7495AfeCE76F41dFc06'},
        'quote': {'symbol': 'USD'}},
    # TWT / BNB
    Address('0x4b0f1812e5df2a09796481ff14017e6005508003'):
    {'feed': {'address': '0x7E728dFA6bCa9023d9aBeE759fDF56BEAb8aC7aD'},
        'quote': {'symbol': 'BNB'}},
    # UNI / BNB
    Address('0xbf5140a22578168fd562dccf235e5d43a02ce9b1'):
    {'feed': {'address': '0x25298F020c3CA1392da76Eb7Ac844813b218ccf7'},
        'quote': {'symbol': 'BNB'}},
    # UNI / USD
    Address('0xbf5140a22578168fd562dccf235e5d43a02ce9b1'):
    {'feed': {'address': '0xb57f259E7C24e56a1dA00F66b55A5640d9f9E7e4'},
        'quote': {'symbol': 'USD'}},
    # USDC / BNB
    Address('0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d'):
    {'feed': {'address': '0x45f86CA2A8BC9EBD757225B19a1A0D7051bE46Db'},
        'quote': {'symbol': 'BNB'}},
    # USDC / USD
    Address('0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d'):
    {'feed': {'address': '0x51597f405303C4377E36123cBc172b13269EA163'},
        'quote': {'symbol': 'USD'}},
    # USDD / USD
    Address('0xd17479997f34dd9156deef8f95a52d81d265be9c'):
    {'feed': {'address': '0x51c78c299C42b058Bf11d47FbB74aC437C6a0c8C'},
        'quote': {'symbol': 'USD'}},
    # USDT / BNB
    Address('0x55d398326f99059ff775485246999027b3197955'):
    {'feed': {'address': '0xD5c40f5144848Bd4EF08a9605d860e727b991513'},
        'quote': {'symbol': 'BNB'}},
    # USDT / USD
    Address('0x55d398326f99059ff775485246999027b3197955'):
    {'feed': {'address': '0xB97Ad0E74fa7d920791E90258A6E2085088b4320'},
        'quote': {'symbol': 'USD'}},
    # VAI / USD
    Address('0x4bd17003473389a42daf6a0a729f6fdb328bbbd7'):
    {'feed': {'address': '0x058316f8Bb13aCD442ee7A216C7b60CFB4Ea1B53'},
        'quote': {'symbol': 'USD'}},
    # VET / USD
    Address('0x6fdcdfef7c496407ccb0cec90f9c5aaa1cc8d888'):
    {'feed': {'address': '0x9f1fD2cEf7b226D555A747DA0411F93c5fe74e13'},
        'quote': {'symbol': 'USD'}},
    # WIN / USD
    Address('0xaef0d72a118ce24fee3cd1d43d383897d05b4e99'):
    {'feed': {'address': '0x9e7377E194E41d63795907c92c3EB351a2eb0233'},
        'quote': {'symbol': 'USD'}},
    # WING / USD
    Address('0x3cb7378565718c64ab86970802140cc48ef1f969'):
    {'feed': {'address': '0xf7E7c0ffCB11dAC6eCA1434C67faB9aE000e10a7'},
        'quote': {'symbol': 'USD'}},
    # WOO / USD
    Address('0x4691937a7508860f876c9c0a2a617e7d9e945d4b'):
    {'feed': {'address': '0x02Bfe714e78E2Ad1bb1C2beE93eC8dc5423B66d4'},
        'quote': {'symbol': 'USD'}},
    # XRP / BNB
    Address('0x1d2f0da169ceb9fc7b3144628db156f3f6c60dbe'):
    {'feed': {'address': '0x798A65D349B2B5E6645695912880b54dfFd79074'},
        'quote': {'symbol': 'BNB'}},
    # XRP / USD
    Address('0x1d2f0da169ceb9fc7b3144628db156f3f6c60dbe'):
    {'feed': {'address': '0x93A67D414896A280bF8FFB3b389fE3686E014fda'},
        'quote': {'symbol': 'USD'}},
    # XTZ / BNB
    Address('0x16939ef78684453bfdfb47825f8a5f714f12623a'):
    {'feed': {'address': '0x8264d6983B219be65C4D62f1c82B3A2999944cF2'},
        'quote': {'symbol': 'BNB'}},
    # XTZ / USD
    Address('0x16939ef78684453bfdfb47825f8a5f714f12623a'):
    {'feed': {'address': '0x9A18137ADCF7b05f033ad26968Ed5a9cf0Bf8E6b'},
        'quote': {'symbol': 'USD'}},
    # XVS / BNB
    Address('0xcf6bb5389c92bdda8a3747ddb454cb7a64626c63'):
    {'feed': {'address': '0xf369A13E7f2449E58DdE8302F008eE9131f8d859'},
        'quote': {'symbol': 'BNB'}},
    # XVS / USD
    Address('0xcf6bb5389c92bdda8a3747ddb454cb7a64626c63'):
    {'feed': {'address': '0xBF63F430A79D4036A5900C19818aFf1fa710f206'},
        'quote': {'symbol': 'USD'}},
    # YFI / BNB
    Address('0x88f1a5ae2a3bf98aeaf342d26b30a79438c9142e'):
    {'feed': {'address': '0xF841761481DF19831cCC851A54D8350aE6022583'},
        'quote': {'symbol': 'BNB'}},
    # YFI / USD
    Address('0x88f1a5ae2a3bf98aeaf342d26b30a79438c9142e'):
    {'feed': {'address': '0xD7eAa5Bf3013A96e3d515c055Dbd98DbdC8c620D'},
        'quote': {'symbol': 'USD'}},
    # YFII / USD
    Address('0x7f70642d88cf1c4a3a7abb072b53b929b653eda5'):
    {'feed': {'address': '0xC94580FAaF145B2FD0ab5215031833c98D3B77E4'},
        'quote': {'symbol': 'USD'}},
    # ZIL / USD
    Address('0xb86abcb37c3a4b64f74f59301aff131a1becc787'):
    {'feed': {'address': '0x3e3aA4FC329529C8Ab921c810850626021dbA7e6'},
        'quote': {'symbol': 'USD'}}
}
