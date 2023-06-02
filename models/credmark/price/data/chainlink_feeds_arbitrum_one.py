from credmark.cmf.types import Address

# The native token on other chain, give a direct address of feed.
CHAINLINK_OVERRIDE_FEED_ARBITRUM_ONE = {
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
}
