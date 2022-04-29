from web3.exceptions import (
    BadFunctionCallOutput
)

from web3._utils.filters import construct_event_filter_params
from web3._utils.events import get_event_data

from credmark.cmf.model.errors import (
    ModelRunError,
)

from credmark.cmf.model import Model
from credmark.cmf.types import (
    Price,
    Token,
    Address,
    Contract,
    Contracts
)
from models.dtos.price import PoolPriceInfo, PoolPriceInfos

from models.dtos.volume import (
    TradingVolume,
    TokenTradingVolume,
)

from models.tmp_abi_lookup import (
    WETH9_ADDRESS,
    DAI_ADDRESS,
    USDC_ADDRESS,
    USDT_ADDRESS,
)


class UniswapV2PoolMeta:
    @staticmethod
    def get_uniswap_pools(model_input, factory_addr):
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
                version='1.1',
                display_name='Uniswap v2 Token Pools',
                description='The Uniswap v2 pools that support a token contract',
                input=Token,
                output=Contracts)
class UniswapV2GetPoolsForToken(Model, UniswapV2PoolMeta):
    # For mainnet, Ropsten, Rinkeby, Görli, and Kovan
    UNISWAP_V2_FACTORY_ADDRESS = {
        k: '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f' for k in [1, 3, 4, 5, 42]}

    def run(self, input: Token) -> Contracts:
        addr = self.UNISWAP_V2_FACTORY_ADDRESS[self.context.chain_id]
        return self.get_uniswap_pools(input, Address(addr).checksum)


class UniswapPoolPriceInfoMeta:
    @staticmethod
    def get_pool_price_infos(model, input, pools_address, pricer_slug) -> PoolPriceInfos:
        """
        Method to be shared between Uniswap V2 and SushiSwap
        """
        pools = [Contract(address=p.address) for p in pools_address]

        prices_with_info = []
        weth_price = None
        for pool in pools:
            reserves = pool.functions.getReserves().call()
            if reserves == [0, 0, 0]:
                continue

            token0 = Token(address=Address(pool.functions.token0().call()).checksum)
            token1 = Token(address=Address(pool.functions.token1().call()).checksum)
            scaled_reserve0 = token0.scaled(reserves[0])
            scaled_reserve1 = token1.scaled(reserves[1])

            if input.address == token0.address:
                inverse = False
                price = scaled_reserve1 / scaled_reserve0
                input_reserve = scaled_reserve0
            else:
                inverse = True
                price = scaled_reserve0 / scaled_reserve1
                input_reserve = scaled_reserve1

            weth_multiplier = 1
            if input.address != WETH9_ADDRESS:
                if WETH9_ADDRESS in (token1.address, token0.address):
                    if weth_price is None:
                        weth_price = model.context.run_model(pricer_slug,
                                                             {"address": WETH9_ADDRESS},
                                                             return_type=Price)
                        if weth_price.price is None:
                            raise ModelRunError('Can not retriev price for WETH')
                    weth_multiplier = weth_price.price

            price *= weth_multiplier

            pool_price_info = PoolPriceInfo(src=model.slug,
                                            price=price,
                                            liquidity=input_reserve,
                                            weth_multiplier=weth_multiplier,
                                            inverse=inverse,
                                            token0_address=token0.address,
                                            token1_address=token1.address,
                                            token0_symbol=token0.symbol,
                                            token1_symbol=token1.symbol,
                                            token0_decimals=token0.decimals,
                                            token1_decimals=token1.decimals,
                                            pool_address=pool.address)
            prices_with_info.append(pool_price_info)

        return PoolPriceInfos(pool_price_infos=prices_with_info)


@Model.describe(slug='uniswap-v2.get-pool-price-info',
                version='1.0',
                display_name='Uniswap v2 Token Pools Price ',
                description='Gather price and liquidity information from pools',
                input=Token,
                output=PoolPriceInfos)
class UniswapV2GetAveragePrice(Model, UniswapPoolPriceInfoMeta):
    def run(self, input: Token) -> PoolPriceInfos:
        pools_address = self.context.run_model('uniswap-v2.get-pools',
                                               input,
                                               return_type=Contracts)

        return self.get_pool_price_infos(self,
                                         input,
                                         pools_address,
                                         pricer_slug='uniswap-v2.get-weighted-price')


@Model.describe(slug='uniswap-v2.pool-volume',
                version='1.1',
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
            # pylint:disable=locally-disabled,protected-access
            swap_event_abi = input.events.Swap._get_event_abi()

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
