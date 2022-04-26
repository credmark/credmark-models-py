from web3.exceptions import (
    BadFunctionCallOutput
)

# TODO: to be merged in framework
from web3._utils.filters import construct_event_filter_params
from web3._utils.events import get_event_data

from credmark.cmf.model import Model
from credmark.cmf.types import (
    Price,
    Token,
    Address,
    Contract,
    Contracts
)

from models.dtos.volume import (
    TradingVolume,
    TokenTradingVolume,
)

from models.tmp_abi_lookup import (
    UNISWAP_V2_FACTORY_ADDRESS,
    WETH9_ADDRESS,
    DAI_ADDRESS,
    USDC_ADDRESS,
    USDT_ADDRESS,
)


def get_uniswap_pools(factory_addr, model_input):
    factory = Contract(address=factory_addr)
    tokens = [Token(symbol='USDC'),
              Token(symbol='USDT'),
              Token(symbol='WETH'),
              Token(symbol='DAI')]

    t2 = [Token(address=Address(USDC_ADDRESS)),
          Token(address=Address(USDT_ADDRESS)),
          Token(address=Address(WETH9_ADDRESS)),
          Token(address=Address(DAI_ADDRESS))]

    for a, b in zip(tokens, t2):
        assert a.address == b.address

    contracts = []
    try:
        for token in tokens:
            pair_address = factory.functions.getPair(model_input.address, token.address).call()
            if not pair_address == Address.null():
                contracts.append(Contract(address=pair_address))
        return Contracts(contracts=contracts)
    except BadFunctionCallOutput:
        # Or use this condition: if self.context.block_number < 10000835 # Uniswap V2
        # Or use this condition: if self.context.block_number < 10794229 # SushiSwap
        return Contracts(contracts=[])


@Model.describe(slug='uniswap-v2.get-pools',
                version='1.0',
                display_name='Uniswap v2 Token Pools',
                description='The Uniswap v2 pools that support a token contract',
                input=Token,
                output=Contracts)
class UniswapV2GetPoolsForToken(Model):

    def run(self, input: Token) -> Contracts:
        return get_uniswap_pools(Address(UNISWAP_V2_FACTORY_ADDRESS), input)


def uniswap_avg_price(model, pools_address, input):
    """
    Method to be shared between Uniswap V2 and SushiSwap
    """
    pools = [Contract(address=p.address) for p in pools_address]

    prices = []
    reserves = []
    weth_price = None
    for pool in pools:
        reserves = pool.functions.getReserves().call()
        if reserves == [0, 0, 0]:
            continue

        token0 = Token(address=pool.functions.token0().call())
        token1 = Token(address=pool.functions.token1().call())
        if input.address == token0.address:
            other_token = Token(address=pool.functions.token1().call())
            token_reserve = reserves[1]
            input_reserve = reserves[0]
        else:
            other_token = Token(address=pool.functions.token0().call())
            token_reserve = reserves[0]
            input_reserve = reserves[1]

        price = other_token.scaled(token_reserve) / input.scaled(input_reserve)

        if input.address != WETH9_ADDRESS:
            if WETH9_ADDRESS in (token0.address, token1.address):
                if weth_price is None:
                    weth_price = model.context.run_model(model.slug,
                                                         {"address": WETH9_ADDRESS},
                                                         return_type=Price).price
                price = price * weth_price
        prices.append((price, input_reserve))

    if len(prices) == 0:
        return Price(price=None, src=model.slug)
    return Price(price=sum([p * r for (p, r) in prices]) / sum([r for (p, r) in prices]),
                 src=model.slug)


@Model.describe(slug='uniswap-v2.get-average-price',
                version='1.0',
                display_name='Uniswap v2 Token Price',
                description='The Uniswap v2 price, averaged by liquidity',
                input=Token,
                output=Price)
class UniswapV2GetAveragePrice(Model):
    def run(self, input: Token) -> Price:
        pools_address = self.context.run_model('uniswap-v2.get-pools',
                                               input,
                                               return_type=Contracts)

        return uniswap_avg_price(self, pools_address, input)


@Model.describe(slug='uniswap-v2.pool-volume',
                version='1.0',
                display_name='Uniswap v2 Pool Swap Volumes',
                description='The volume of each token swapped in a pool in a window',
                input=Contract,
                output=TradingVolume)
class UniswapV2PoolSwapVolume(Model):
    def run(self, input: Contract) -> TradingVolume:
        input = Contract(address=input.address)

        token0 = Token(address=input.functions.token0().call())
        token1 = Token(address=input.functions.token1().call())

        try:
            swaps = input.events.Swap.createFilter(
                fromBlock=self.context.block_number - int(86400 / 14),
                toBlock=self.context.block_number).get_all_entries()
        except ValueError:
            # Some node server does not support newer eth_newFilter method
            # Alternatively, use protected method
            # input.events._get_event_abi()
            swap_event_abi = [x for x in input.events.abi
                              if 'name' in x and x['name'] == 'Swap' and
                                 'type' in x and x['type'] == 'event'][0]

            __data_filter_set, event_filter_params = construct_event_filter_params(
                abi_codec=self.context.web3.codec,
                event_abi=swap_event_abi,
                address=input.address.checksum,
                fromBlock=self.context.block_number - int(86400 * 10 / 14),
                toBlock=self.context.block_number
            )
            swaps = self.context.web3.eth.get_logs(event_filter_params)
            swaps = [get_event_data(self.context.web3.codec, swap_event_abi, s) for s in swaps]

        return TradingVolume(
            tokenVolumes=[
                TokenTradingVolume(
                    token=token0,
                    sellAmount=sum([s['args']['amount0In'] for s in swaps]),
                    buyAmount=sum([s['args']['amount0Out'] for s in swaps])),
                TokenTradingVolume(
                    token=token1,
                    sellAmount=sum([s['args']['amount1In'] for s in swaps]),
                    buyAmount=sum([s['args']['amount1Out'] for s in swaps]))
            ])
