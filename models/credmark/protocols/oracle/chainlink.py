from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import Contract, Price
from credmark.dto import DTO, DTOField, EmptyInput
from ens import ENS
from models.dtos.price import Maybe, PriceInput
from web3.exceptions import ContractLogicError


@Model.describe(slug='chainlink.get-feed-registry',
                version="1.0",
                display_name="Chainlink - Feed registry",
                description="Supports multi-chain",
                input=EmptyInput,
                output=Contract)
class ChainLinkFeedRegistry(Model):
    CHAINLINK_REGISTRY = {
        1: '0x47Fb2585D2C56Fe188D0E6ec628a38b74fCeeeDf',
        42: '0xAa7F6f7f507457a1EE157fE97F6c7DB2BEec5cD0'
    }

    def run(self, _) -> Contract:
        registry = Contract(address=self.CHAINLINK_REGISTRY[self.context.chain_id])
        _ = registry.abi
        return registry


class ENSDomainName(DTO):
    domain: str = DTOField(description='ENS Domain nam')


# TODO: implement shortest path
@Model.describe(slug='chainlink.price-by-ens',
                version="1.0",
                display_name="Chainlink - Price by ENS",
                description="Use ENS domain name for a token pair",
                input=ENSDomainName,
                output=Price)
class ChainLinkPriceByENS(Model):
    def run(self, input: ENSDomainName) -> Price:
        ns = ENS.fromWeb3(self.context.web3)
        feed_address = ns.address(input.domain)
        if feed_address is None:
            raise ModelRunError('Unable to resolve ENS domain name {input.domain}')
        return self.context.run_model('chainlink.price-by-feed',
                                      input=Account(address=Address(feed_address)),
                                      return_type=Price)


@ Model.describe(slug='chainlink.price-by-feed',
                 version="1.0",
                 display_name="Chainlink - Price by feed",
                 description="Input a Chainlink valid feed",
                 input=Account,
                 output=Price)
class ChainLinkPriceByFeed(Model):
    def run(self, input: Account) -> Price:
        feed_contract = Contract(address=input.address)
        (_roundId, answer,
            _startedAt, _updatedAt,
            _answeredInRound) = feed_contract.functions.latestRoundData().call()
        decimals = feed_contract.functions.decimals().call()
        description = feed_contract.functions.description().call()
        version = feed_contract.functions.version().call()

        feed = None
        if feed_contract.abi is not None:
            abi_funcs = [x['name'].lower()  # type: ignore
                         for x in feed_contract.abi
                         if 'name' in x]
            if 'aggregator'.lower() in abi_funcs:
                feed = feed_contract.functions.aggregator().call()

        if feed is None:
            feed = input.address
        isFeedEnabled = None

        time_diff = self.context.block_number.timestamp - _updatedAt
        round_diff = _answeredInRound - _roundId
        return Price(price=answer / (10 ** decimals),
                     src=(f'{self.slug}|{description}|{feed}|v{version}|'
                          f'{isFeedEnabled}|t:{time_diff}s|r:{round_diff}'))


@Model.describe(slug='chainlink.price-from-registry-maybe',
                version="1.1",
                display_name="Chainlink - Price by Registry",
                description="Looking up Registry for two tokens' addresses",
                input=PriceInput,
                output=Maybe[Price])
class ChainLinkFeedFromRegistryMaybe(Model):
    def run(self, input: PriceInput) -> Maybe[Price]:
        try:
            price = self.context.run_model('chainlink.price-by-registry',
                                           input=input,
                                           return_type=Price)
            return Maybe[Price](just=price)
        except ModelRunError as _err:
            try:
                price = self.context.run_model('chainlink.price-by-registry',
                                               input=input.inverse(),
                                               return_type=Price).inverse()
                return Maybe[Price](just=price)
            except ModelRunError as _err2:
                return Maybe[Price](just=None)


@Model.describe(slug='chainlink.price-by-registry',
                version="1.2",
                display_name="Chainlink - Price by Registry",
                description="Looking up Registry for two tokens' addresses",
                input=PriceInput,
                output=Price)
class ChainLinkPriceByRegistry(Model):
    def run(self, input: Tokens) -> Price:
        token0_address = input.tokens[0].address
        token1_address = input.tokens[1].address

        registry = self.context.run_model('chainlink.get-feed-registry',
                                          input=EmptyInput(),
                                          return_type=Contract)

        feed = registry.functions.getFeed(token0_address, token1_address).call()
        (_roundId, answer,
            _startedAt, _updatedAt,
            _answeredInRound) = (registry.functions.latestRoundData(token0_address, token1_address)
                                 .call())
        decimals = registry.functions.decimals(token0_address, token1_address).call()
        description = registry.functions.description(token0_address, token1_address).call()
        version = registry.functions.version(token0_address, token1_address).call()
        isFeedEnabled = registry.functions.isFeedEnabled(feed).call()

        time_diff = self.context.block_number.timestamp - _updatedAt
        round_diff = _answeredInRound - _roundId
        return Price(price=answer / (10 ** decimals),
                     src=(f'{self.slug}|{description}|{feed}|v{version}|'
                          f'{isFeedEnabled}|t:{time_diff}s|r:{round_diff}'))


@Model.describe(slug='chainlink.price-usd',
                version="1.2",
                display_name="Chainlink - Price for Token / USD pair",
                description="Input a Token",
                input=Token,
                output=Price)
class ChainLinkFeedPriceUSD(Model):
    ETH = Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE')
    BTC = Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB')

    # 0x0000000000000000000000000000000000000348
    USD = Address('0x{:040x}'.format(840))
    # 0x000000000000000000000000000000000000033a
    GBP = Address('0x{:040x}'.format(826))
    # 0x00000000000000000000000000000000000003d2
    EUR = Address('0x{:040x}'.format(978))

    # TODO: need to find the address to find the feed in registry
    OVERRIDE_FEED = {
        1: {
            # WAVAX: avax-usd.data.eth
            Address('0x85f138bfEE4ef8e540890CFb48F620571d67Eda3'):
            '0xFF3EEb22B5E3dE6e705b44749C2559d704923FD7',
            # WSOL: sol-usd.data.eth
            Address('0xD31a59c85aE9D8edEFeC411D448f90841571b89c'):
            '0x4ffc43a60e009b551865a93d232e33fce9f01507',
            # BNB: bnb-usd.data.eth
            Address('0xB8c77482e45F1F44dE1745F52C74426C631bDD52'):
            '0x14e613ac84a31f709eadbdf89c6cc390fdc9540a',
            # WBTC:
            Address('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'):
            '0xf4030086522a5beea4988f8ca5b36dbc97bee88c',
            # WETH:
            Address('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'):
            '0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419'
        }
    }

    ROUTING_FEED = {
        1: {
            Address('0x767FE9EDC9E0dF98E07454847909b5E959D7ca0E'):
            ['0xf600984cca37cd562e74e3ee514289e3613ce8e4',  # ilv-eth.data.eth
             '0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419'],
            Address('0x383518188C0C6d7730D91b2c03a03C837814a899'):  # OHM v1
            ['0x90c2098473852e2f07678fe1b6d595b1bd9b16ed',   # ohm-eth.data.eth
             '0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419'],  # eth-usd.data.eth
            Address('0x64aa3364F17a4D01c6f1751Fd97C2BD3D7e7f1D5'):
            ['0x9a72298ae3886221820b1c878d12d872087d3a23',   # ohmv2-eth.data.eth
             '0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419'],  # eth-usd.data.eth
            Address('0xc7283b66Eb1EB5FB86327f08e1B5816b0720212B'):
            ['0x84a24deca415acc0c395872a9e6a63e27d6225c8',  # tribe-eth.data.eth
             '0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419'],
        }
    }

    CONVERT_FOR_TOKEN_PRICE = {
        1: {
            Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
            Address('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'),
            Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'):
            Address('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'),
        }
    }

    def run(self, input: Token) -> Price:
        override_feed = self.OVERRIDE_FEED[self.context.chain_id].get(input.address, None)
        routing_feed = self.ROUTING_FEED[self.context.chain_id].get(input.address, None)
        try:
            if override_feed is not None:
                return self.context.run_model('chainlink.price-by-feed',
                                              input=Account(address=Address(override_feed)),
                                              return_type=Price)
            elif routing_feed is not None:
                sources = []
                p = Price(price=1.0, src='')
                for rout in routing_feed:
                    new_piece = self.context.run_model('chainlink.price-by-feed',
                                                       input=Account(address=Address(rout)),
                                                       return_type=Price)
                    p.price *= new_piece.price
                    sources.append(new_piece.src)
                p.src = '.'.join(sources)
                return p
            else:
                tokens = [Token(address=input.address), Token(address=self.USD)]
                return self.context.run_model('chainlink.price-by-registry',
                                              input=Tokens(tokens=tokens),
                                              return_type=Price)
        except ModelRunError as err:
            if 'Feed not found' in str(err):
                self.logger.info(f'No feed found for {base_address}/{quote_address}')
                raise ModelRunError(f'No feed found for {base_address}/{quote_address}')
            raise err
        finally:
            del sys.tracebacklimit
