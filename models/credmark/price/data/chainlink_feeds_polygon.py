from credmark.cmf.types import Address

CHAINLINK_OVERRIDE_FEED_POLYGON = {
    # 1INCH / USD
    Address('0x9c2c5fd7b07e95ee044ddeba0e97a665f142394f'):
    {'feed': {'address': '0x443C5116CdF663Eb387e72C688D276e702135C87'},
        'quote': {'symbol': 'USD'}},
    # AAVE / ETH
    Address('0xd6df932a45c0f255f85145f286ea0b292b21c90b'):
    {'feed': {'address': '0xbE23a3AA13038CfC28aFd0ECe4FdE379fE7fBfc4'},
        'quote': {'symbol': 'ETH'}},
    # AAVE / USD
    Address('0xd6df932a45c0f255f85145f286ea0b292b21c90b'):
    {'feed': {'address': '0x72484B12719E23115761D5DA1646945632979bB6'},
        'quote': {'symbol': 'USD'}},
    # AGEUR / USD
    Address('0xe0b52e49357fd4daf2c15e02058dce6bc0057db4'):
    {'feed': {'address': '0x9b88d07B2354eF5f4579690356818e07371c7BeD'},
        'quote': {'symbol': 'USD'}},
    # ALCX / USD
    Address('0x95c300e7740d2a88a44124b424bfc1cb2f9c3b89'):
    {'feed': {'address': '0x5DB6e61B6159B20F068dc15A47dF2E5931b14f29'},
        'quote': {'symbol': 'USD'}},
    # ALPHA / USD
    Address('0x6a3e7c3c6ef65ee26975b12293ca1aad7e1daed2'):
    {'feed': {'address': '0x289833F252eaB98582D62db94Bd75aB48AD9CF0D'},
        'quote': {'symbol': 'USD'}},
    # ANT / USD
    Address('0x2b8504ab5efc246d0ec5ec7e74565683227497de'):
    {'feed': {'address': '0x213b030E24C906ee3b98EC7538Cc6D3D3C82aF55'},
        'quote': {'symbol': 'USD'}},
    # APE / USD
    Address('0xb7b31a6bc18e48888545ce79e83e06003be70930'):
    {'feed': {'address': '0x2Ac3F3Bfac8fC9094BC3f0F9041a51375235B992'},
        'quote': {'symbol': 'USD'}},
    # AVAX / USD
    Address('0x2c89bbc92bd86f8075d1decc58c7f4e0107f286b'):
    {'feed': {'address': '0xe01eA2fbd8D76ee323FbEd03eB9a8625EC981A10'},
        'quote': {'symbol': 'USD'}},
    # AXS / USD
    Address('0x61bdd9c7d4df4bf47a4508c0c8245505f2af5b7b'):
    {'feed': {'address': '0x9c371aE34509590E10aB98205d2dF5936A1aD875'},
        'quote': {'symbol': 'USD'}},
    # BADGER / ETH
    Address('0x1fcbe5937b0cc2adf69772d228fa4205acf4d9b2'):
    {'feed': {'address': '0x82C9d4E88862f194C2bd874a106a90dDD0D35AAB'},
        'quote': {'symbol': 'ETH'}},
    # BADGER / USD
    Address('0x1fcbe5937b0cc2adf69772d228fa4205acf4d9b2'):
    {'feed': {'address': '0xF626964Ba5e81405f47e8004F0b276Bb974742B5'},
        'quote': {'symbol': 'USD'}},
    # BAL / ETH
    Address('0x9a71012b13ca4d3d0cdc72a177df3ef03b0e76a3'):
    {'feed': {'address': '0x03CD157746c61F44597dD54C6f6702105258C722'},
        'quote': {'symbol': 'ETH'}},
    # BAL / USD
    Address('0x9a71012b13ca4d3d0cdc72a177df3ef03b0e76a3'):
    {'feed': {'address': '0xD106B538F2A868c28Ca1Ec7E298C3325E0251d66'},
        'quote': {'symbol': 'USD'}},
    # BAT / USD
    Address('0x3cef98bb43d732e2f285ee605a8158cde967d219'):
    {'feed': {'address': '0x2346Ce62bd732c62618944E51cbFa09D985d86D2'},
        'quote': {'symbol': 'USD'}},
    # BNB / USD
    Address('0xa649325aa7c5093d12d6f98eb4378deae68ce23f'):
    {'feed': {'address': '0x82a6c4AF830caa6c97bb504425f6A66165C2c26e'},
        'quote': {'symbol': 'USD'}},
    # BNT / USD
    Address('0xc26d47d5c33ac71ac5cf9f776d63ba292a4f7842'):
    {'feed': {'address': '0xF5724884b6E99257cC003375e6b844bC776183f9'},
        'quote': {'symbol': 'USD'}},
    # BOND / USD
    Address('0xa041544fe2be56cce31ebb69102b965e06aace80'):
    {'feed': {'address': '0x58527C2dCC755297bB81f9334b80b2B6032d8524'},
        'quote': {'symbol': 'USD'}},
    # BTC / ETH
    Address('0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'):
    {'feed': {'address': '0x19b0F0833C78c0848109E3842D34d2fDF2cA69BA'},
        'quote': {'symbol': 'ETH'}},
    # BTC / USD
    Address('0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'):
    {'feed': {'address': '0xc907E116054Ad103354f2D350FD2514433D57F6f'},
        'quote': {'symbol': 'USD'}},
    # BUSD / USD
    Address('0xdab529f40e671a1d4bf91361c21bf9f0c9712ab7'):
    {'feed': {'address': '0xE0dC07D5ED74741CeeDA61284eE56a2A0f7A4Cc9'},
        'quote': {'symbol': 'USD'}},
    # CEL / USD
    Address('0xd85d1e945766fea5eda9103f918bd915fbca63e6'):
    {'feed': {'address': '0xc9ECF45956f576681bDc01F79602A79bC2667B0c'},
        'quote': {'symbol': 'USD'}},
    # CHZ / USD
    Address('0xf1938ce12400f9a761084e7a80d37e732a4da056'):
    {'feed': {'address': '0x2409987e514Ad8B0973C2b90ee1D95051DF0ECB9'},
        'quote': {'symbol': 'USD'}},
    # COMP / USD
    Address('0x8505b9d2254a7ae468c0e9dd10ccea3a837aef5c'):
    {'feed': {'address': '0x2A8758b7257102461BC958279054e372C2b1bDE6'},
        'quote': {'symbol': 'USD'}},
    # CRV / ETH
    Address('0x172370d5cd63279efa6d502dab29171933a610af'):
    {'feed': {'address': '0x1CF68C76803c9A415bE301f50E82e44c64B7F1D4'},
        'quote': {'symbol': 'ETH'}},
    # CRV / USD
    Address('0x172370d5cd63279efa6d502dab29171933a610af'):
    {'feed': {'address': '0x336584C8E6Dc19637A5b36206B1c79923111b405'},
        'quote': {'symbol': 'USD'}},
    # CVX / USD
    Address('0x4257ea7637c355f81616050cbb6a9b709fd72683'):
    {'feed': {'address': '0x5ec151834040B4D453A1eA46aA634C1773b36084'},
        'quote': {'symbol': 'USD'}},
    # DAI / ETH
    Address('0x8f3cf7ad23cd3cadbd9735aff958023239c6a063'):
    {'feed': {'address': '0xFC539A559e170f848323e19dfD66007520510085'},
        'quote': {'symbol': 'ETH'}},
    # DAI / USD
    Address('0x8f3cf7ad23cd3cadbd9735aff958023239c6a063'):
    {'feed': {'address': '0x4746DeC9e833A82EC7C2C1356372CcF2cfcD2F3D'},
        'quote': {'symbol': 'USD'}},
    # DODO / USD
    Address('0xe4bf2864ebec7b7fdf6eeca9bacae7cdfdaffe78'):
    {'feed': {'address': '0x59161117086a4C7A9beDA16C66e40Bdaa1C5a8B6'},
        'quote': {'symbol': 'USD'}},
    # DPI / USD
    Address('0x85955046df4668e1dd369d2de9f3aeb98dd2a369'):
    {'feed': {'address': '0x2e48b7924FBe04d575BA229A59b64547d9da16e9'},
        'quote': {'symbol': 'USD'}},
    # ENJ / USD
    Address('0x7ec26842f195c852fa843bb9f6d8b583a274a157'):
    {'feed': {'address': '0x440A341bbC9FA86aA60A195e2409a547e48d4C0C'},
        'quote': {'symbol': 'USD'}},
    # ETH / USD
    Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
    {'feed': {'address': '0xF9680D99D6C9589e2a93a78A04A279e509205945'},
        'quote': {'symbol': 'USD'}},
    # FIS / USD
    Address('0x7a7b94f18ef6ad056cda648588181cda84800f94'):
    {'feed': {'address': '0x18617D05eE1692Ad7EAFee9839459da16097AFd8'},
        'quote': {'symbol': 'USD'}},
    # FRAX / USD
    Address('0x45c32fa6df82ead1e2ef74d17b76547eddfaff89'):
    {'feed': {'address': '0x00DBeB1e45485d53DF7C2F0dF1Aa0b6Dc30311d3'},
        'quote': {'symbol': 'USD'}},
    # FTM / USD
    Address('0xc9c1c1c20b3658f8787cc2fd702267791f224ce1'):
    {'feed': {'address': '0x58326c0F831b2Dbf7234A4204F28Bba79AA06d5f'},
        'quote': {'symbol': 'USD'}},
    # FXS / USD
    Address('0x1a3acf6d19267e2d3e7f898f42803e90c9219062'):
    {'feed': {'address': '0x6C0fe985D3cAcbCdE428b84fc9431792694d0f51'},
        'quote': {'symbol': 'USD'}},
    # GHST / ETH
    Address('0x385eeac5cb85a38a9a07a70c73e0a3271cfb54a7'):
    {'feed': {'address': '0xe638249AF9642CdA55A92245525268482eE4C67b'},
        'quote': {'symbol': 'ETH'}},
    # GHST / USD
    Address('0x385eeac5cb85a38a9a07a70c73e0a3271cfb54a7'):
    {'feed': {'address': '0xDD229Ce42f11D8Ee7fFf29bDB71C7b81352e11be'},
        'quote': {'symbol': 'USD'}},
    # GRT / USD
    Address('0x5fe2b58c013d7601147dcdd68c143a77499f5531'):
    {'feed': {'address': '0x3FabBfb300B1e2D7c9B84512fe9D30aeDF24C410'},
        'quote': {'symbol': 'USD'}},
    # KAVA / USD
    Address('0x87d32f2c0a3d6d091772890c81e321026454a125'):
    {'feed': {'address': '0x7899dd75C329eFe63e35b02bC7d60D3739FB23c5'},
        'quote': {'symbol': 'USD'}},
    # KNC / USD
    Address('0x1c954e8fe737f99f68fa1ccda3e51ebdb291948c'):
    {'feed': {'address': '0x10e5f3DFc81B3e5Ef4e648C4454D04e79E1E41E2'},
        'quote': {'symbol': 'USD'}},
    # LINK / ETH
    Address('0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39'):
    {'feed': {'address': '0xb77fa460604b9C6435A235D057F7D319AC83cb53'},
        'quote': {'symbol': 'ETH'}},
    # LINK / MATIC
    Address('0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39'):
    {'feed': {'address': '0x5787BefDc0ECd210Dfa948264631CD53E68F7802'},
        'quote': {'symbol': 'MATIC'}},
    # LINK / USD
    Address('0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39'):
    {'feed': {'address': '0xd9FFdb71EbE7496cC440152d43986Aae0AB76665'},
        'quote': {'symbol': 'USD'}},
    # LPT / USD
    Address('0x3962f4a0a0051dcce0be73a7e09cef5756736712'):
    {'feed': {'address': '0xBAaF11CeDA1d1Ca9Cf01748F8196653c9656a400'},
        'quote': {'symbol': 'USD'}},
    # MANA / USD
    Address('0xa1c57f48f0deb89f569dfbe6e2b7f46d33606fd4'):
    {'feed': {'address': '0xA1CbF3Fe43BC3501e3Fc4b573e822c70e76A7512'},
        'quote': {'symbol': 'USD'}},
    # MATIC / ETH
    Address('0x0000000000000000000000000000000000001010'):
    {'feed': {'address': '0x327e23A4855b6F663a28c5161541d69Af8973302'},
        'quote': {'symbol': 'ETH'}},
    # MATIC / USD
    Address('0x0000000000000000000000000000000000001010'):
    {'feed': {'address': '0xAB594600376Ec9fD91F8e885dADF0CE036862dE0'},
        'quote': {'symbol': 'USD'}},
    # MIM / USD
    Address('0x49a0400587a7f65072c87c4910449fdcc5c47242'):
    {'feed': {'address': '0xd133F916e04ed5D67b231183d85Be12eAA018320'},
        'quote': {'symbol': 'USD'}},
    # MIMATIC / USD
    Address('0xa3fa99a148fa48d14ed51d610c367c61876997f1'):
    {'feed': {'address': '0xd8d483d813547CfB624b8Dc33a00F2fcbCd2D428'},
        'quote': {'symbol': 'USD'}},
    # MKR / ETH
    Address('0x6f7c932e7684666c9fd1d44527765433e01ff61d'):
    {'feed': {'address': '0x807b59d12520830D1864286FA0271c27baa94197'},
        'quote': {'symbol': 'ETH'}},
    # MKR / USD
    Address('0x6f7c932e7684666c9fd1d44527765433e01ff61d'):
    {'feed': {'address': '0xa070427bF5bA5709f70e98b94Cb2F435a242C46C'},
        'quote': {'symbol': 'USD'}},
    # MLN / ETH
    Address('0xa9f37d84c856fda3812ad0519dad44fa0a3fe207'):
    {'feed': {'address': '0xB89D583B72aBF9C3a7e6e093251C2fCad3365312'},
        'quote': {'symbol': 'ETH'}},
    # NEXO / USD
    Address('0x41b3966b4ff7b427969ddf5da3627d6aeae9a48e'):
    {'feed': {'address': '0x666bb13b3ED3816504E8c30D0F9B9C16b371774b'},
        'quote': {'symbol': 'USD'}},
    # OGN / USD
    Address('0xa63beffd33ab3a2efd92a39a7d2361cee14ceba8'):
    {'feed': {'address': '0x8Ec0eC2e0F26D8253ABf39Db4B1793D76B49C6D5'},
        'quote': {'symbol': 'USD'}},
    # OM / USD
    Address('0xc3ec80343d2bae2f8e680fdadde7c17e71e114ea'):
    {'feed': {'address': '0xc86105DccF9BD629Cea7Fd41f94c6050bF96D57F'},
        'quote': {'symbol': 'USD'}},
    # OMG / USD
    Address('0x62414d03084eeb269e18c970a21f45d2967f0170'):
    {'feed': {'address': '0x93FfEE768F74208a7b9f2a4426f0F6BCbb1D09de'},
        'quote': {'symbol': 'USD'}},
    # PAXG / USD
    Address('0x553d3d295e0f695b9228246232edf400ed3560b5'):
    {'feed': {'address': '0x0f6914d8e7e1214CDb3A4C6fbf729b75C69DF608'},
        'quote': {'symbol': 'USD'}},
    # PLA / USD
    Address('0x8765f05adce126d70bcdf1b0a48db573316662eb'):
    {'feed': {'address': '0x24C0e0FC8cCb21e2fb3e1A8A4eC4b29458664f79'},
        'quote': {'symbol': 'USD'}},
    # QUICK / ETH
    Address('0xb5c064f955d8e7f38fe0460c556a72987494ee17'):
    {'feed': {'address': '0x836a579B39d22b2147c1C229920d27880C915578'},
        'quote': {'symbol': 'ETH'}},
    # QUICK / USD
    Address('0xb5c064f955d8e7f38fe0460c556a72987494ee17'):
    {'feed': {'address': '0xa058689f4bCa95208bba3F265674AE95dED75B6D'},
        'quote': {'symbol': 'USD'}},
    # RAI / USD
    Address('0x00e5646f60ac6fb446f621d146b6e1886f002905'):
    {'feed': {'address': '0x7f45273fD7C644714825345670414Ea649b50b16'},
        'quote': {'symbol': 'USD'}},
    # SAND / USD
    Address('0xbbba073c31bf03b8acf7c28ef0738decf3695683'):
    {'feed': {'address': '0x3D49406EDd4D52Fb7FFd25485f32E073b529C924'},
        'quote': {'symbol': 'USD'}},
    # SHIB / USD
    Address('0x6f8a06447ff6fcf75d803135a7de15ce88c1d4ec'):
    {'feed': {'address': '0x3710abeb1A0Fc7C2EC59C26c8DAA7a448ff6125A'},
        'quote': {'symbol': 'USD'}},
    # SLP / USD
    Address('0x0c7304fbaf2a320a1c50c46fe03752722f729946'):
    {'feed': {'address': '0xBB3eF70953fC3766bec4Ab7A9BF05B6E4caf89c6'},
        'quote': {'symbol': 'USD'}},
    # SNX / USD
    Address('0x50b728d8d964fd00c2d0aad81718b71311fef68a'):
    {'feed': {'address': '0xbF90A5D9B6EE9019028dbFc2a9E50056d5252894'},
        'quote': {'symbol': 'USD'}},
    # SOL / USD
    Address('0xd93f7e271cb87c23aaa73edc008a79646d1f9912'):
    {'feed': {'address': '0x10C8264C0935b3B9870013e057f330Ff3e9C56dC'},
        'quote': {'symbol': 'USD'}},
    # STORJ / USD
    Address('0xd72357daca2cf11a5f155b9ff7880e595a3f5792'):
    {'feed': {'address': '0x0F1d5Bd7be9B30Fc09E110cd6504Bd450e53cb0E'},
        'quote': {'symbol': 'USD'}},
    # SUSHI / ETH
    Address('0x0b3f868e0be5597d5db7feb59e1cadbb0fdda50a'):
    {'feed': {'address': '0x17414Eb5159A082e8d41D243C1601c2944401431'},
        'quote': {'symbol': 'ETH'}},
    # SUSHI / USD
    Address('0x0b3f868e0be5597d5db7feb59e1cadbb0fdda50a'):
    {'feed': {'address': '0x49B0c695039243BBfEb8EcD054EB70061fd54aa0'},
        'quote': {'symbol': 'USD'}},
    # TUSD / USD
    Address('0x2e1ad108ff1d8c782fcbbb89aad783ac49586756'):
    {'feed': {'address': '0x7C5D415B64312D38c56B54358449d0a4058339d2'},
        'quote': {'symbol': 'USD'}},
    # UMA / USD
    Address('0x3066818837c5e6ed6601bd5a91b0762877a6b731'):
    {'feed': {'address': '0x33D9B1BAaDcF4b26ab6F8E83e9cb8a611B2B3956'},
        'quote': {'symbol': 'USD'}},
    # UNI / ETH
    Address('0xb33eaad8d922b1083446dc23f610c2567fb5180f'):
    {'feed': {'address': '0x162d8c5bF15eB6BEe003a1ffc4049C92114bc931'},
        'quote': {'symbol': 'ETH'}},
    # UNI / USD
    Address('0xb33eaad8d922b1083446dc23f610c2567fb5180f'):
    {'feed': {'address': '0xdf0Fb4e4F928d2dCB76f438575fDD8682386e13C'},
        'quote': {'symbol': 'USD'}},
    # USDC / ETH
    Address('0x2791bca1f2de4661ed88a30c99a7a9449aa84174'):
    {'feed': {'address': '0xefb7e6be8356cCc6827799B6A7348eE674A80EaE'},
        'quote': {'symbol': 'ETH'}},
    # USDC / USD
    Address('0x2791bca1f2de4661ed88a30c99a7a9449aa84174'):
    {'feed': {'address': '0xfE4A8cc5b5B2366C1B58Bea3858e81843581b2F7'},
        'quote': {'symbol': 'USD'}},
    # USDT / ETH
    Address('0xc2132d05d31c914a87c6611c10748aeb04b58e8f'):
    {'feed': {'address': '0xf9d5AAC6E5572AEFa6bd64108ff86a222F69B64d'},
        'quote': {'symbol': 'ETH'}},
    # USDT / USD
    Address('0xc2132d05d31c914a87c6611c10748aeb04b58e8f'):
    {'feed': {'address': '0x0A6513e40db6EB1b165753AD52E80663aeA50545'},
        'quote': {'symbol': 'USD'}},
    # WOO / USD
    Address('0x1b815d120b3ef02039ee11dc2d33de7aa4a8c603'):
    {'feed': {'address': '0x6a99EC84819FB7007dd5D032068742604E755c56'},
        'quote': {'symbol': 'USD'}},
    # WSTETH / ETH
    Address('0x03b54a6e9a984069379fae1a4fc4dbae93b3bccd'):
    {'feed': {'address': '0x10f964234cae09cB6a9854B56FF7D4F38Cda5E6a'},
        'quote': {'symbol': 'ETH'}},
    # YFI / ETH
    Address('0xda537104d6a5edd53c6fbba9a898708e465260b6'):
    {'feed': {'address': '0x9896A1eA7A00F5f32Ab131eBbeE07487B0af31D0'},
        'quote': {'symbol': 'ETH'}},
    # YFI / USD
    Address('0xda537104d6a5edd53c6fbba9a898708e465260b6'):
    {'feed': {'address': '0x9d3A43c111E7b2C6601705D9fcF7a70c95b1dc55'},
        'quote': {'symbol': 'USD'}},
    # ZRX / USD
    Address('0x5559edb74751a0ede9dea4dc23aee72cca6be3d5'):
    {'feed': {'address': '0x6EA4d89474d9410939d429B786208c74853A5B47'},
        'quote': {'symbol': 'USD'}}
}
