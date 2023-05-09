from credmark.cmf.types import Address

CHAINLINK_OVERRIDE_FEED_POLYGON = {
    # WETH / USD
    Address('0x7ceb23fd6bc0add59e62ac25578270cff1b9f619'):
    {'feed': {'address': '0xf9680d99d6c9589e2a93a78a04a279e509205945'},
     'quote': {'symbol': 'USD'}},
    # ETH / USD
    Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
    {'feed': {'address': '0xf9680d99d6c9589e2a93a78a04a279e509205945'},
        'quote': {'symbol': 'USD'}},
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
        'quote': {'symbol': 'WETH'}},
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
    # LINK with mapper (used by Uniswap) / USD
    Address('0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39'):
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
    # WMATIC / USD
    Address('0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270'):
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
}
