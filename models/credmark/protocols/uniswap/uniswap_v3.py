import credmark.model
from credmark.types import Address, AddressDTO
from credmark.types.dto import DTO
from ....tmp_abi_lookup import (DAI_ADDRESS, UNISWAP_V3_FACTORY_ABI,
                                UNISWAP_V3_FACTORY_ADDRESS, UNISWAP_V3_POOL_ABI, USDT_ADDRESS,
                                WETH9_ADDRESS, USDC_ADDRESS, MIN_ERC20_ABI)


class UniswapV3PoolInfo(DTO):
    address: Address
    sqrtPriceX96: str
    tick: int
    observationIndex: int
    observationCardinality: int
    observationCardinalityNext: int
    feeProtocol: int
    unlocked: bool
    liquidity: str
    fee: int
    token0: Address
    token1: Address


@credmark.model.describe(slug='uniswap-v3-get-pools',
                         version='1.0',
                         display_name='Uniswap v3 Token Pools',
                         description='The Uniswap v3 pools that support a token contract',
                         input=AddressDTO)
class UniswapV3GetPoolsForToken(credmark.model.Model):

    def run(self, input: AddressDTO) -> dict:
        """
        We should be able to hit the IQuoter Interface to get the quoted price from Uniswap.
        Block_number should be taken care of.
        """
        fees = [500, 3000, 10000]
        primary_tokens = [DAI_ADDRESS, WETH9_ADDRESS, USDC_ADDRESS, USDT_ADDRESS]

        if self.context.chain_id != 1:
            return {}

        uniswap_factory = self.context.web3.eth.contract(
            address=Address(UNISWAP_V3_FACTORY_ADDRESS).checksum,
            abi=UNISWAP_V3_FACTORY_ABI)

        pools = []

        for fee in fees:
            for primary_token in primary_tokens:
                pool = uniswap_factory.functions.getPool(
                    input.address, primary_token, fee).call()
                if pool != "0x0000000000000000000000000000000000000000":
                    pools.append(pool)

        return {"result": pools}


@credmark.model.describe(slug='uniswap-v3-get-pool-info',
                         version='1.0',
                         display_name='Uniswap v3 Token Pools',
                         description='The Uniswap v3 pools that support a token contract',
                         input=AddressDTO,
                         output=UniswapV3PoolInfo)
class UniswapV3GetPoolInfo(credmark.model.Model):
    def run(self, input: AddressDTO) -> UniswapV3PoolInfo:
        pool = self.context.web3.eth.contract(
            address=input.address.checksum,
            abi=UNISWAP_V3_POOL_ABI
        )
        slot0 = pool.functions.slot0().call()
        token0 = pool.functions.token0().call()
        token1 = pool.functions.token1().call()
        liquidity = pool.functions.liquidity().call()
        fee = pool.functions.fee().call()
        res = {
            "address": input.address,
            "sqrtPriceX96": slot0[0],
            "tick": slot0[1],
            "observationIndex": slot0[2],
            "observationCardinality": slot0[3],
            "observationCardinalityNext": slot0[4],
            "feeProtocol": slot0[5],
            "unlocked": slot0[6],
            "token0": token0,
            "token1": token1,
            "liquidity": liquidity,
            "fee": fee
        }

        return UniswapV3PoolInfo(**res)


@ credmark.model.describe(slug='uniswap-v3-get-average-price',
                          version='1.0',
                          display_name='Uniswap v3 Token Pools',
                          description='The Uniswap v3 pools that support a token contract',
                          input=AddressDTO)
class UniswapV3GetAveragePrice(credmark.model.Model):
    def run(self, input: AddressDTO) -> dict:
        pools = self.context.run_model(
            'uniswap-v3-get-pools', {"address": input.address.checksum})
        infos = [self.context.run_model('uniswap-v3-get-pool-info',
                                        {"address": p}) for p in pools['result']]
        prices = []
        for info in infos:
            decimal0 = self.context.web3.eth.contract(
                address=info['token0'], abi=MIN_ERC20_ABI).functions.decimals().call()
            decimal1 = self.context.web3.eth.contract(
                address=info['token1'], abi=MIN_ERC20_ABI).functions.decimals().call()
            tick_price = 1.0001 ** info['tick'] * (10 ** (decimal0 - decimal1))

            if input.address == info['token1']:
                tick_price = 1/tick_price
            if input.address != WETH9_ADDRESS:
                if info['token1'] == WETH9_ADDRESS or info['token0'] == WETH9_ADDRESS:
                    tick_price = tick_price * \
                        self.context.run_model('uniswap-v3-get-average-price',
                                               {"address": WETH9_ADDRESS})['price']

            prices.append(tick_price)
        price = sum(prices) / len(prices)
        return {"price": price}


@ credmark.model.describe(slug='uniswap-v3-get-30-day-price',
                          version='1.0',
                          display_name='Uniswap v3 Token Pools',
                          description='The Uniswap v3 pools that support a token contract',
                          input=AddressDTO)
class UniswapV3GetAveragePrice30Day(credmark.model.Model):

    def run(self, input) -> dict:
        return self.context.historical.run_model_historical('uniswap-v3-get-average-price', window='30 days', model_input=input)
