from web3.exceptions import (
    BadFunctionCallOutput
)

# TODO: to be merged in framework
from web3._utils.filters import construct_event_filter_params
from web3._utils.events import get_event_data

import credmark.model
from credmark.types import (
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
    UNISWAP_V2_SWAP_ABI,
    UNISWAP_V2_FACTORY_ADDRESS,
)


@credmark.model.describe(slug='uniswap-v2.get-pools',
                         version='1.0',
                         display_name='Uniswap v2 Token Pools',
                         description='The Uniswap v2 pools that support a token contract',
                         input=Token,
                         output=Contracts)
class UniswapV2GetPoolsForToken(credmark.model.Model):

    def run(self, input: Token) -> Contracts:

        factory = Contract(address=UNISWAP_V2_FACTORY_ADDRESS)
        tokens = [Token(symbol="USDC"),
                  Token(symbol="WETH"),
                  Token(symbol="DAI")]
        contracts = []
        try:
            for token in tokens:
                pair_address = factory.functions.getPair(input.address, token.address).call()
                if not pair_address == Address.null():
                    contracts.append(Contract(address=pair_address))
            return Contracts(contracts=contracts)
        except BadFunctionCallOutput:
            # Or use this condition: if self.context.block_number < 10000835
            return Contracts(contracts=[])


@credmark.model.describe(slug='uniswap-v2.get-average-price',
                         version='1.0',
                         display_name='Uniswap v2 Token Price',
                         description='The Uniswap v2 price, averaged by liquidity',
                         input=Token,
                         output=Price)
class UniswapV2GetAveragePrice(credmark.model.Model):
    def run(self, input: Token) -> Price:
        pools = self.context.run_model('uniswap-v2.get-pools', input, return_type=Contracts)

        # TODO: remove abi
        pools = [Contract(address=p.address,  abi=UNISWAP_V2_SWAP_ABI) for p in pools]

        prices = []
        reserves = []
        weth_price = None
        for pool in pools:
            reserves = pool.functions.getReserves().call()
            if reserves == [0, 0, 0]:
                continue
            if input.address == pool.functions.token0().call():
                token1 = Token(address=pool.functions.token1().call())
                reserve = reserves[0]
                price = token1.scaled(reserves[1]) / input.scaled(reserves[0])

                if token1.symbol == 'WETH':
                    if weth_price is None:
                        weth_price = self.context.run_model('uniswap-v2.get-average-price',
                                                            token1,
                                                            return_type=Price).price
                    price = price * weth_price
            else:
                token0 = Token(address=pool.functions.token0().call())
                reserve = reserves[1]
                price = token0.scaled(reserves[0]) / input.scaled(reserves[1])
                if token0.symbol == 'WETH':
                    if weth_price is None:
                        weth_price = self.context.run_model('uniswap-v2.get-average-price',
                                                            token0,
                                                            return_type=Price).price
                    price = price * weth_price
            prices.append((price, reserve))
        if len(prices) == 0:
            return Price(price=None, src='uniswap_v2')
        return Price(price=sum([p * r for (p, r) in prices]) / sum([r for (p, r) in prices]),
                     src='uniswap_v2')


@credmark.model.describe(slug='uniswap-v2.pool-volume',
                         version='1.0',
                         display_name='Uniswap v2 Pool Swap Volumes',
                         description='The volume of each token swapped in a pool in a window',
                         input=Contract,
                         output=TradingVolume)
class UniswapV2PoolSwapVolume(credmark.model.Model):
    def run(self, input: Contract) -> TradingVolume:
        input = Contract(address=input.address, abi=UNISWAP_V2_SWAP_ABI)

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
