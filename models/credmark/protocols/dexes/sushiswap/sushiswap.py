import credmark.model
from credmark.types import (
    Address,
    Contract,
    Token,
    Contracts,
    Price
)
from credmark.dto import (
    DTO
)

from models.tmp_abi_lookup import (
    SUSHISWAP_FACTORY_ADDRESS,
    SUSHISWAP_FACTORY_ABI,
    SUSHISWAP_PAIRS_ABI,
    ERC_20_TOKEN_CONTRACT_ABI,
    UNISWAP_V2_SWAP_ABI,
    ERC_20_ABI,
)


@credmark.model.describe(slug="sushiswap.all-pools",
                         version="1.0",
                         display_name="Sushiswap all pairs",
                         description="Returns the addresses of all pairs on Suhsiswap protocol")
class SushiswapAllPairs(credmark.model.Model):
    def run(self, input) -> dict:

        contract = Contract(
            address=Address(SUSHISWAP_FACTORY_ADDRESS).checksum,
            abi=SUSHISWAP_FACTORY_ABI
        )

        allPairsLength = contract.functions.allPairsLength().call()

        sushiswap_pairs_addresses = []

        error_count = 0
        for i in range(allPairsLength):
            try:
                pair_address = contract.functions.allPairs(i).call()
                sushiswap_pairs_addresses.append(Address(pair_address).checksum)

            except Exception as _err:
                error_count += 1

        return {"result": sushiswap_pairs_addresses}


class SushiSwapPool(DTO):
    token0: Token
    token1: Token


@credmark.model.describe(slug="sushiswap.get-pool",
                         version="1.0",
                         display_name="Sushiswap get pool for a pair of tokens",
                         description=("Returns the addresses of the pool of "
                                      "both tokens on Suhsiswap protocol"),
                         input=SushiSwapPool)
class SushiswapGetPair(credmark.model.Model):
    def run(self, input: SushiSwapPool):
        self.logger.info(f'{input=}')
        contract = Contract(
            address=Address(SUSHISWAP_FACTORY_ADDRESS).checksum,
            abi=SUSHISWAP_FACTORY_ABI
        )

        if input.token0.address and input.token1.address:
            token0 = input.token0.address.checksum
            token1 = input.token1.address.checksum

            pair_pool = contract.functions.getPair(token0, token1).call()
            return {'pool': pair_pool}
        else:
            return {}


@credmark.model.describe(slug="sushiswap.get-pool-info",
                         version="1.0",
                         display_name="Sushiswap get details for a pool",
                         description="Returns the token details of the pool",
                         input=Contract)
class SushiswapGetPairDetails(credmark.model.Model):
    def try_or(self, func, default=None, expected_exc=(Exception,)):
        try:
            return func()
        except expected_exc:
            return default

    def run(self, input: Contract):
        output = {}
        self.logger.info(f'{input=}')
        contract = Contract(
            address=input.address.checksum,
            abi=SUSHISWAP_PAIRS_ABI
        )
        token0 = contract.functions.token0().call()
        token1 = contract.functions.token1().call()
        getReserves = contract.functions.getReserves().call()

        token0_instance = Contract(
            address=token0, abi=ERC_20_TOKEN_CONTRACT_ABI)
        _token0_name = self.try_or(lambda: token0_instance.functions.name().call())
        _token0_symbol = self.try_or(lambda: token0_instance.functions.symbol().call())
        _token0_decimals = token0_instance.functions.decimals().call()

        token1_instance = Contract(
            address=token1, abi=ERC_20_TOKEN_CONTRACT_ABI)
        _token1_name = self.try_or(lambda: token1_instance.functions.name().call())
        _token1_symbol = self.try_or(lambda: token1_instance.functions.symbol().call())
        _token1_decimals = token1_instance.functions.decimals().call()

        token0_reserve = getReserves[0]/pow(10, _token0_decimals)
        token1_reserve = getReserves[1]/pow(10, _token1_decimals)

        output = {'pairAddress': input.address,
                  'token0': token0,
                  'token0_name': _token0_name,
                  'token0_symbol': _token0_symbol,
                  'token0_reserve': token0_reserve,
                  'token1': token1,
                  'token1_name': _token1_name,
                  'token1_symbol': _token1_symbol,
                  'token1_reserve': token1_reserve}

        return output


@credmark.model.describe(slug='sushiswap.get-pools',
                         version='1.1',
                         display_name='Uniswap v2 Token Pools',
                         description='The Uniswap v2 pools that support a token contract',
                         input=Token,
                         output=Contracts)
class SushiswapGetPoolsForToken(credmark.model.Model):

    def run(self, input: Token) -> Contracts:

        factory = Contract(address=SUSHISWAP_FACTORY_ADDRESS)
        tokens = [Token(symbol="USDC"),
                  Token(symbol="WETH"),
                  Token(symbol="DAI")]
        contracts = []
        for token in tokens:
            pair_address = factory.functions.getPair(input.address, token.address).call()
            if not pair_address == Address.null():
                contracts.append(Contract(address=pair_address))
        return Contracts(contracts=contracts)


@credmark.model.describe(slug='sushiswap.get-average-price',
                         version='1.0',
                         display_name='Sushiswap Token Price',
                         description='The Sushiswap price, averaged by liquidity',
                         input=Token,
                         output=Price)
class SushiswapGetAveragePrice(credmark.model.Model):
    def run(self, input: Token) -> Price:
        # FIXME: remove ABI
        input = Token(address=input.address, abi=ERC_20_ABI)

        pools = self.context.run_model('sushiswap.get-pools',
                                       input,
                                       return_type=Contracts)
        # FIXME: remove ABI
        pools = [Contract(address=p.address, abi=UNISWAP_V2_SWAP_ABI) for p in pools]

        prices = []
        reserves = []
        weth_price = None
        for pool in pools:
            reserves = pool.functions.getReserves().call()
            if input.address == pool.functions.token0().call():
                # FIXME: remove ABI
                token1 = Token(address=pool.functions.token1().call(), abi=ERC_20_ABI)

                reserve = reserves[0]
                price = token1.scaled(reserves[1]) / input.scaled(reserves[0])

                if token1.symbol == 'WETH':
                    if weth_price is None:
                        weth_price = self.context.run_model('sushiswap.get-average-price',
                                                            token1,
                                                            return_type=Price).price
                    price = price * weth_price
            else:
                # FIXME: remove ABI
                token0 = Token(address=pool.functions.token0().call(), abi=ERC_20_ABI)
                reserve = reserves[1]
                price = token0.scaled(reserves[0]) / input.scaled(reserves[1])
                if token0.symbol == 'WETH':
                    if weth_price is None:
                        weth_price = self.context.run_model('sushiswap.get-average-price',
                                                            token0,
                                                            return_type=Price).price
                    price = price * weth_price
            prices.append((price, reserve))
        if len(prices) == 0:
            return Price(price=None)
        return Price(price=sum([p * r for (p, r) in prices]) / sum([r for (p, r) in prices]))
