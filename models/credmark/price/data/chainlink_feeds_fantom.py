from credmark.cmf.types import Address

# The native token on other chain, give a direct address of feed.
CHAINLINK_OVERRIDE_FEED_FANTOM = {
    # AAVE / USD
    Address('0x6a07a792ab2965c72a5b8088d3a069a7ac3a993b'):
    {'feed': {'address': '0xE6ecF7d2361B6459cBb3b4fb065E0eF4B175Fe74'},
        'quote': {'symbol': 'USD'}},
    # ALPACA / USD
    Address('0xad996a45fd2373ed0b10efa4a8ecb9de445a4302'):
    {'feed': {'address': '0x95d3FFf86A754AB81A7c59FcaB1468A2076f8C9b'},
        'quote': {'symbol': 'USD'}},
    # BIFI / USD
    Address('0xd6070ae98b8069de6b494332d1a1a81b6179d960'):
    {'feed': {'address': '0x4F5Cc6a2291c964dEc4C7d6a50c0D89492d4D91B'},
        'quote': {'symbol': 'USD'}},
    # BNB / USD
    Address('0xd67de0e0a0fd7b15dc8348bb9be742f3c5850454'):
    {'feed': {'address': '0x6dE70f4791C4151E00aD02e969bD900DC961f92a'},
        'quote': {'symbol': 'USD'}},
    # BOO / USD
    Address('0x841fad6eae12c286d1fd18d1d525dffa75c7effe'):
    {'feed': {'address': '0xc8C80c17f05930876Ba7c1DD50D9186213496376'},
        'quote': {'symbol': 'USD'}},
    # BTC / USD
    Address('0x321162cd933e2be498cd2267a90534a804051b11'):
    {'feed': {'address': '0x8e94C22142F4A64b99022ccDd994f4e9EC86E4B4'},
        'quote': {'symbol': 'USD'}},
    # CREAM / USD
    Address('0x657a1861c15a3ded9af0b6799a195a249ebdcbc6'):
    {'feed': {'address': '0xD2fFcCfA0934caFdA647c5Ff8e7918A10103c01c'},
        'quote': {'symbol': 'USD'}},
    # CRV / USD
    Address('0x1e4f97b9f9f913c46f1632781732927b9019c68b'):
    {'feed': {'address': '0xa141D7E3B44594cc65142AE5F2C7844Abea66D2B'},
        'quote': {'symbol': 'USD'}},
    # DAI / USD
    Address('0x8d11ec38a3eb5e956b052f67da8bdc9bef8abf3e'):
    {'feed': {'address': '0x91d5DEFAFfE2854C7D02F50c80FA1fdc8A721e52'},
        'quote': {'symbol': 'USD'}},
    # ETH / USD
    Address('0x74b23882a30290451a17c44f4f05243b6b58c76d'):
    {'feed': {'address': '0x11DdD3d147E5b83D01cee7070027092397d63658'},
        'quote': {'symbol': 'USD'}},
    # FRAX / USD
    Address('0xdc301622e621166bd8e82f2ca0a26c13ad0be355'):
    {'feed': {'address': '0xBaC409D670d996Ef852056f6d45eCA41A8D57FbD'},
        'quote': {'symbol': 'USD'}},
    # FTM / USD
    Address('0xFFfFfFffFFfffFFfFFfFFFFFffFFFffffFfFFFfF'):
    {'feed': {'address': '0xf4766552D15AE4d256Ad41B6cf2933482B0680dc'},
        'quote': {'symbol': 'USD'}},
    # LINK / FTM
    Address('0xb3654dc3d10ea7645f8319668e8f54d2574fbdc8'):
    {'feed': {'address': '0x3FFe75E8EDA86F48e454e6bfb5F74d95C20744f4'},
        'quote': {'symbol': 'FTM'}},
    # LINK / USD
    Address('0xb3654dc3d10ea7645f8319668e8f54d2574fbdc8'):
    {'feed': {'address': '0x221C773d8647BC3034e91a0c47062e26D20d97B4'},
        'quote': {'symbol': 'USD'}},
    # MIM / USD
    Address('0x82f0b8b456c1a451378467398982d4834b6829c1'):
    {'feed': {'address': '0x28de48D3291F31F839274B8d82691c77DF1c5ceD'},
        'quote': {'symbol': 'USD'}},
    # MIMATIC / USD
    Address('0xfb98b335551a418cd0737375a2ea0ded62ea213b'):
    {'feed': {'address': '0x827863222c9C603960dE6FF2c0dD58D457Dcc363'},
        'quote': {'symbol': 'USD'}},
    # SNX / USD
    Address('0x56ee926bd8c72b2d5fa1af4d9e4cbb515a1e3adc'):
    {'feed': {'address': '0x2Eb00cC9dB7A7E0a013A49b3F6Ac66008d1456F7'},
        'quote': {'symbol': 'USD'}},
    # SPELL / USD
    Address('0x468003b688943977e6130f4f68f23aad939a1040'):
    {'feed': {'address': '0x02E48946849e0BFDD7bEa5daa80AF77195C7E24c'},
        'quote': {'symbol': 'USD'}},
    # SUSHI / USD
    Address('0xae75a438b2e0cb8bb01ec1e1e376de11d44477cc'):
    {'feed': {'address': '0xCcc059a1a17577676c8673952Dc02070D29e5a66'},
        'quote': {'symbol': 'USD'}},
    # USDC / USD
    Address('0x04068da6c83afcfa0e13ba15a6696662335d5b75'):
    {'feed': {'address': '0x2553f4eeb82d5A26427b8d1106C51499CBa5D99c'},
        'quote': {'symbol': 'USD'}},
    # YFI / USD
    Address('0x29b0da86e484e1c0029b56e817912d778ac0ec69'):
    {'feed': {'address': '0x9B25eC3d6acfF665DfbbFD68B3C1D896E067F0ae'},
        'quote': {'symbol': 'USD'}}
}
