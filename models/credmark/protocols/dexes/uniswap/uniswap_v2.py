from typing import (
    Union,
    Optional,
)

import credmark.model
from credmark.dto import (
    DTO,
)
from credmark.types import (
    Price,
    Token,
    Address,
    Contract,
    Contracts
)
from models.dtos.volume import TradingVolume, TokenTradingVolume
from models.tmp_abi_lookup import (
    UNISWAP_V2_SWAP_ABI,
    ERC_20_ABI,
)
UNISWAP_V2_FACTORY_ADDRESS = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"


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
        for token in tokens:
            pair_address = factory.functions.getPair(input.address, token.address).call()
            if not pair_address == Address.null():
                contracts.append(Contract(address=pair_address))
        return Contracts(contracts=contracts)


@credmark.model.describe(slug='uniswap-v2.get-average-price',
                         version='1.0',
                         display_name='Uniswap v2 Token Price',
                         description='The Uniswap v2 price, averaged by liquidity',
                         input=Token,
                         output=Price)
class UniswapV2GetAveragePrice(credmark.model.Model):
    def run(self, input: Token) -> Price:
        # FIXME: remove ABI
        if input.address == Address('0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2'):
            # FIXME: MKR abi for symol
            input = Token(address=input.address, abi='[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"stop","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"owner_","type":"address"}],"name":"setOwner","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"src","type":"address"},{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"wad","type":"uint256"}],"name":"burn","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"name_","type":"bytes32"}],"name":"setName","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"src","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"stopped","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"authority_","type":"address"}],"name":"setAuthority","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"burn","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"wad","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"push","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"src","type":"address"},{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"move","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[],"name":"start","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"authority","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"src","type":"address"},{"name":"guy","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"src","type":"address"},{"name":"wad","type":"uint256"}],"name":"pull","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"symbol_","type":"bytes32"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"name":"guy","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"guy","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Burn","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"authority","type":"address"}],"name":"LogSetAuthority","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"owner","type":"address"}],"name":"LogSetOwner","type":"event"},{"anonymous":true,"inputs":[{"indexed":true,"name":"sig","type":"bytes4"},{"indexed":true,"name":"guy","type":"address"},{"indexed":true,"name":"foo","type":"bytes32"},{"indexed":true,"name":"bar","type":"bytes32"},{"indexed":false,"name":"wad","type":"uint256"},{"indexed":false,"name":"fax","type":"bytes"}],"name":"LogNote","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"from","type":"address"},{"indexed":true,"name":"to","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"owner","type":"address"},{"indexed":true,"name":"spender","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Approval","type":"event"}]')
        else:
            input = Token(address=input.address, abi=ERC_20_ABI)

        pools = self.context.run_model('uniswap-v2.get-pools', input, return_type=Contracts)

        # FIXME: remove abi
        pools = [Contract(address=p.address,  abi=UNISWAP_V2_SWAP_ABI) for p in pools]

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
                        weth_price = self.context.run_model('uniswap-v2.get-average-price',
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
                        weth_price = self.context.run_model('uniswap-v2.get-average-price',
                                                            token0,
                                                            return_type=Price).price
                    price = price * weth_price
            prices.append((price, reserve))
        if len(prices) == 0:
            return Price(price=None)
        return Price(price=sum([p * r for (p, r) in prices]) / sum([r for (p, r) in prices]))


@credmark.model.describe(slug='uniswap-v2.pool-volume',
                         version='1.0',
                         display_name='Uniswap v2 Pool Swap Volumes',
                         description='The volume of each token swapped in a pool in a window',
                         input=Contract,
                         output=TradingVolume)
class UniswapV2PoolSwapVolume(credmark.model.Model):
    def run(self, input: Contract) -> TradingVolume:
        input = Contract(address=input.address, abi=UNISWAP_V2_SWAP_ABI)
        swaps = input.events.Swap.createFilter(
            fromBlock=self.context.block_number - int(86400 / 14),
            toBlock=self.context.block_number).get_all_entries()
        token0 = Token(address=input.functions.token0().call())
        token1 = Token(address=input.functions.token1().call())
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
