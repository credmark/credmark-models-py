from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import (ModelDataError, ModelInputError,
                                       ModelRunError)
from credmark.cmf.types import Address, Currency, Maybe, Network, Price, PriceWithQuote
from models.dtos.price import PriceInput

PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='No possible feed/routing for token pair')


@Model.describe(slug='price.oracle-chainlink-maybe',
                version='1.3',
                display_name='Token Price - from Oracle',
                description='Get token\'s price from Oracle - return None if not found',
                category='protocol',
                subcategory='chainlink',
                tags=['price'],
                input=PriceInput,
                output=Maybe[PriceWithQuote])
class PriceOracleChainlinkMaybe(Model):
    def run(self, input: PriceInput) -> Maybe[PriceWithQuote]:
        try:
            price = self.context.run_model('price.oracle-chainlink',
                                           input=input,
                                           return_type=PriceWithQuote,
                                           local=True)
            return Maybe[PriceWithQuote](just=price)
        except ModelRunError:
            return Maybe.none()


@Model.describe(slug='price.oracle-chainlink',
                version='1.11',
                display_name='Token Price - from Oracle',
                description='Get token\'s price from Oracle',
                category='protocol',
                subcategory='chainlink',
                tags=['price'],
                input=PriceInput,
                output=PriceWithQuote,
                errors=PRICE_DATA_ERROR_DESC)
class PriceOracleChainlink(Model):
    # The native token on other chain, give a direct address of feed.
    # TODO: find the token address so to find the feed in Chainlink's registry
    OVERRIDE_FEED = {
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
            # ZEC: using BSC's contract address
            Address('0x1ba42e5193dfa8b03d15dd1b86a3113bbbef8eeb'):
            {'feed': {'address': '0x6EA4d89474d9410939d429B786208c74853A5B47'},
             'quote': {'symbol': 'USD'}},
        }
    }

    ROUTING_ADDRESSES = [
        Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'),  # ETH
        Address('0x0000000000000000000000000000000000000348'),  # USD
        Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'),  # BTC
    ]

    WRAP_TOKEN = {
        Network.Mainnet: {
            # WETH => ETH
            Address('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'):
            {'symbol': 'ETH'},
            # BTC => WBTC
            Address('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'):
            {'symbol': 'BTC'},
        },
        Network.BSC: {},
        Network.Polygon: {},
    }

    """
    Return the value of base token in amount of quote tokens
    """

    def check_wrap(self, token):
        if token.address in self.WRAP_TOKEN[self.context.network]:
            return Currency(**self.WRAP_TOKEN[self.context.network][token.address])
        return token

    def replace_input(self, input):
        new_input = PriceInput(base=input.base, quote=input.quote)
        new_input.base = self.check_wrap(new_input.base)
        new_input.quote = self.check_wrap(new_input.quote)
        return new_input

    # pylint: disable=too-many-return-statements, too-many-branches
    def run(self, input: PriceInput) -> PriceWithQuote:
        new_input = self.replace_input(input)
        base = new_input.base
        quote = new_input.quote

        if base.address is None or quote.address is None:
            raise ModelInputError(f'{input} does not carry valid address')

        if base == quote:
            return PriceWithQuote(price=1, src=f'{self.slug}|Equal', quoteAddress=quote.address)

        if self.context.chain_id == Network.Mainnet:
            price_maybe = self.context.run_model('chainlink.price-from-registry-maybe',
                                                 input=new_input,
                                                 return_type=Maybe[PriceWithQuote],
                                                 local=True)
            if price_maybe.just is not None:
                return price_maybe.just

        try_override_base = self.OVERRIDE_FEED[self.context.network].get(base.address, None)
        if try_override_base is not None:
            if 'ens' in try_override_base:
                override_ens = try_override_base['ens']
                override_quote = Currency(**try_override_base['quote'])

                p0 = self.context.run_model('chainlink.price-by-ens',
                                            input=override_ens,
                                            return_type=Price,
                                            local=True)
            elif 'feed' in try_override_base:
                override_feed = try_override_base['feed']
                override_quote = Currency(**try_override_base['quote'])

                p0 = self.context.run_model('chainlink.price-by-feed',
                                            input=override_feed,
                                            return_type=Price,
                                            local=True)
            else:
                raise ModelRunError(f'Unknown override {try_override_base}')

            pq0 = PriceWithQuote(**p0.dict(), quoteAddress=quote.address)

            if override_quote.address == quote.address:
                return pq0
            else:
                pq1 = self.context.run_model(self.slug,
                                             input={'base': override_quote, 'quote': quote},
                                             return_type=PriceWithQuote)
                return pq0.cross(pq1)

        try_override_quote = self.OVERRIDE_FEED[self.context.network].get(quote.address, None)
        if try_override_quote is not None:
            if 'ens' in try_override_quote:
                override_ens = try_override_quote['ens']
                override_quote = Currency(**try_override_quote['quote'])

                p0 = self.context.run_model('chainlink.price-by-ens',
                                            input=override_ens,
                                            return_type=Price,
                                            local=True)
            elif 'feed' in try_override_quote:
                override_feed = try_override_quote['feed']
                override_quote = Currency(**try_override_quote['quote'])

                p0 = self.context.run_model('chainlink.price-by-feed',
                                            input=override_feed,
                                            return_type=Price,
                                            local=True)
            else:
                raise ModelRunError(f'Unknown override {try_override_quote}')

            pq0 = PriceWithQuote(**p0.dict(), quoteAddress=quote.address).inverse(quote.address)
            if override_quote.address == base.address:
                return pq0
            else:
                pq1 = self.context.run_model(self.slug,
                                             input={'base': override_quote, 'quote': base},
                                             return_type=PriceWithQuote)
                pq1 = pq1.inverse(override_quote.address)
            return pq0.cross(pq1)

        p1 = None
        r1 = None
        for rt_addr in self.ROUTING_ADDRESSES:
            if rt_addr not in (quote.address, base.address):
                price_input = PriceInput(base=base, quote=Currency(address=rt_addr))

                pq1_maybe = self.context.run_model('chainlink.price-from-registry-maybe',
                                                   input=price_input,
                                                   return_type=Maybe[PriceWithQuote],
                                                   local=True)
                if pq1_maybe.just is not None:
                    p1 = pq1_maybe.just
                    r1 = rt_addr
                    break

        if p1 is not None:
            p2 = None
            r2 = None
            for rt_addr in self.ROUTING_ADDRESSES:
                if rt_addr not in (quote.address, base.address):
                    price_input = PriceInput(base=Currency(address=rt_addr), quote=quote)

                    pq2_maybe = self.context.run_model('chainlink.price-from-registry-maybe',
                                                       input=price_input,
                                                       return_type=Maybe[PriceWithQuote],
                                                       local=True)
                    if pq2_maybe.just is not None:
                        p2 = pq2_maybe.just
                        r2 = rt_addr
                        break

            if p2 is not None:
                if r1 == r2:
                    return p1.cross(p2)
                else:
                    bridge_price = self.context.run_model(
                        self.slug,
                        input={'base': {"address": r1},
                               'quote': {"address": r2}},
                        return_type=PriceWithQuote)
                    return p1.cross(bridge_price).cross(p2)

        if new_input == input:
            raise ModelRunError(f'No possible feed/routing for token pair '
                                f'{input.base}/{input.quote}')

        raise ModelRunError(f'No possible feed/routing for token pair '
                            f'{input.base}/{input.quote}, '
                            f'replaced by {new_input.base}/{new_input.quote}')
