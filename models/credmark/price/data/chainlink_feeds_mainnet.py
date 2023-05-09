from credmark.cmf.types import Address

# The native token on other chain, give a direct address of feed.
# TODO: find the token address so to find the feed in Chainlink's registry
CHAINLINK_OVERRIDE_FEED_MAINNET = {
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
}
