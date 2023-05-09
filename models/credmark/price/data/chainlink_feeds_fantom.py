from credmark.cmf.types import Address

# The native token on other chain, give a direct address of feed.
# TODO: find the token address so to find the feed in Chainlink's registry
CHAINLINK_OVERRIDE_FEED_FANTOM = {
    # AAVE / USD
    Address('0x6a07a792ab2965c72a5b8088d3a069a7ac3a993b'):
    {'feed': {'address': '0xaDc59a292c274B438BD29de01897B07D40E9b408'},
     'quote': {'symbol': 'USD'}},
    # ALPACA / USD
    Address('0xad996a45fd2373ed0b10efa4a8ecb9de445a4302'):
    {'feed': {'address': '0xd867c068534Ad7d3BE0fE4f321AACddCe371DB1A'},
     'quote': {'symbol': 'USD'}},
    # BIFI / USD
    Address('0xd6070ae98b8069de6b494332d1a1a81b6179d960'):
    {'feed': {'address': '0xc7439cd23025a798913a027Fb46bc347021483Db'},
     'quote': {'symbol': 'USD'}},
    # BNB / USD
    Address('0xd67de0e0a0fd7b15dc8348bb9be742f3c5850454'):
    {'feed': {'address': '0x5Cd752a9493630cFbb6F545c78D342D638E90Fe3'},
     'quote': {'symbol': 'USD'}},
    # BOO / USD
    Address('0x841fad6eae12c286d1fd18d1d525dffa75c7effe'):
    {'feed': {'address': '0x8173d07C6b085Ae79326Fd6Dd514ab5966c3248c'},
     'quote': {'symbol': 'USD'}},
    # BTC / USD
    Address('0x321162cd933e2be498cd2267a90534a804051b11'):
    {'feed': {'address': '0x472105bB154bD92580a9669AB2483864c3dE9974'},
     'quote': {'symbol': 'USD'}},
    # CREAM / USD
    Address('0x657a1861c15a3ded9af0b6799a195a249ebdcbc6'):
    {'feed': {'address': '0x2946220288DbBF77dF0030fCecc2a8348CbBE32C'},
     'quote': {'symbol': 'USD'}},
    # CRV / USD
    Address('0x1e4f97b9f9f913c46f1632781732927b9019c68b'):
    {'feed': {'address': '0xbfc6236cE03765739Db1393421C0d7675eeD8D7D'},
     'quote': {'symbol': 'USD'}},
    # DAI / USD
    Address('0x8d11ec38a3eb5e956b052f67da8bdc9bef8abf3e'):
    {'feed': {'address': '0x15e682Ba1F3e68D507Eb8D21F2D2a90bA82559Ae'},
     'quote': {'symbol': 'USD'}},
    # ETH / USD
    Address('0x74b23882a30290451a17c44f4f05243b6b58c76d'):
    {'feed': {'address': '0x50f8339E5668F85Bcb4D8DF987C12b7Df4c99084'},
     'quote': {'symbol': 'USD'}},
    # FRAX / USD
    Address('0xdc301622e621166bd8e82f2ca0a26c13ad0be355'):
    {'feed': {'address': '0xc2bD6467d9567Cfaf2783d7DE5F337bf98Fe62C1'},
     'quote': {'symbol': 'USD'}},
    # LINK / USD
    Address('0xb3654dc3d10ea7645f8319668e8f54d2574fbdc8'):
    {'feed': {'address': '0xF13148424cc6fDfa793eAe323B081c130fF839F1'},
     'quote': {'symbol': 'USD'}},
    # MIM / USD
    Address('0x82f0b8b456c1a451378467398982d4834b6829c1'):
    {'feed': {'address': '0x50a0a7C4066336203488c877958A8D7D3ab946FE'},
     'quote': {'symbol': 'USD'}},
    # MIMATIC / USD
    Address('0xfb98b335551a418cd0737375a2ea0ded62ea213b'):
    {'feed': {'address': '0x42A70DC2cfCa080Da3a2568a3EC3A51E6E76363F'},
     'quote': {'symbol': 'USD'}},
    # SNX / USD
    Address('0x56ee926bd8c72b2d5fa1af4d9e4cbb515a1e3adc'):
    {'feed': {'address': '0x1F0C026D3f87b0c69e3c8399A53b8Da4aA6304C2'},
     'quote': {'symbol': 'USD'}},
    # SPELL / USD
    Address('0x468003b688943977e6130f4f68f23aad939a1040'):
    {'feed': {'address': '0x421CfF3FF719b5101f9c8Da487445C39838A566c'},
     'quote': {'symbol': 'USD'}},
    # SUSHI / USD
    Address('0xae75a438b2e0cb8bb01ec1e1e376de11d44477cc'):
    {'feed': {'address': '0x649F04a23eE3708331A949395b61F37b3Fd94847'},
     'quote': {'symbol': 'USD'}},
    # USDC / USD
    Address('0x04068da6c83afcfa0e13ba15a6696662335d5b75'):
    {'feed': {'address': '0x9C5a8b11CeE8c207753C313a566761526F2c7934'},
     'quote': {'symbol': 'USD'}},
    # YFI / USD
    Address('0x29b0da86e484e1c0029b56e817912d778ac0ec69'):
    {'feed': {'address': '0x0cEe0aee5C6C0d1f99829E9Debf6F3cE39266160'},
     'quote': {'symbol': 'USD'}}
}
