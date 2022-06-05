from datetime import datetime, timedelta, timezone, date
from typing import Tuple
from credmark.cmf.model import Model
from credmark.cmf.types import (
    Address,
    Contract,
    Token,
)
from credmark.cmf.model.errors import ModelDataError
from credmark.dto import (
    DTO,
)


from models.tmp_abi_lookup import (
    UNISWAP_V3_POOL_ABI,
)
# Function to catch naming error while fetching mandatory data


def try_or(func, default=None, expected_exc=(Exception,)):
    try:
        return func()
    except expected_exc:
        return default


class PoolVolumeInfo(Contract):
    name: str
    address: Address
    coin_balances: dict
    prices: dict
    tvl: float
    volume24h: float


class PoolVolumeInfoHistoricalInput(DTO):
    pool_address: Contract
    date_range: Tuple[date, date]


@Model.describe(slug="contrib.curve-get-tvl-and-volume",
                version="1.0",
                display_name="Get TVL and Volume for a Curve's pool",
                description="Get TVL and Volume for a Curve's pool",
                input=Contract,
                output=PoolVolumeInfo)
class CurveGetTVLAndVolume(Model):
    def run(self, input: Contract) -> PoolVolumeInfo:
        # Converting to CheckSum Address
        pool = Address(input.address).checksum
        # Pool name
        pool_name = str('None')
        # Dict of coin balances
        coin_balances = {}
        # Dict of prices
        prices = {}
        # Total Value Locked
        tvl = float(0)
        # Volume in Past 24 Hours
        volume24h = float(0)
        # Initiating the contract instance
        pool_contract_instance = Contract(address=pool)
        # Number of tokens in pool (Initial no. of tokens=2)
        n = 2
        # initiating token counter and token adresses of each asset in pool
        token0 = pool_contract_instance.functions.coins(0).call()
        token1 = pool_contract_instance.functions.coins(1).call()
        # If third token present
        token2 = try_or(lambda: pool_contract_instance.functions.coins(2).call())
        # If fourth token present
        token3 = try_or(lambda: pool_contract_instance.functions.coins(3).call())

        # Fetching token0 and token1 details and balance
        token0_instance = Token(address=token0)
        token0_name, token0_symbol = token0_instance.name, token0_instance.symbol
        token0_balance = token0_instance.scaled(token0_instance.functions.balanceOf(pool).call())
        coin_balances.update({token0_symbol: token0_balance})
        token0_price = self.context.run_model(
            slug='price.cmf',
            input=token0_instance
        )
        tvl += token0_balance * token0_price['price']
        prices.update({token0_symbol: token0_price['price']})
        token1_instance = Token(address=token1)
        token1_name, token1_symbol = token1_instance.name, token1_instance.symbol
        token1_balance = token1_instance.scaled(token1_instance.functions.balanceOf(pool).call())
        coin_balances.update({token1_symbol: token1_balance})
        token1_price = self.context.run_model(
            slug='price.cmf',
            input=token1_instance
        )
        tvl += token1_balance * token1_price['price']
        prices.update({token1_symbol: token1_price['price']})

        # Pool Name
        pool_name = 'Curve.fi : {}-{}/{}-{}'.format(
            str(token0_name), str(token0_symbol),
            str(token1_name), str(token1_symbol)
        )

        # Fetching token2 details if present in thee pool
        if token2 is None:
            pass
        else:
            token2_instance = Token(address=token2)
            token2_name, token2_symbol = token2_instance.name, token2_instance.symbol
            token2_balance = token2_instance.scaled(
                token2_instance.functions.balanceOf(pool).call()
            )
            # Updating coins
            coin_balances.update({token2_symbol: token2_balance})
            # Updating number of tokens present
            n += 1
            # Updating pool name
            pool_name = pool_name + '/{}-{}'.format(str(token2_name), str(token2_symbol))
            token2_price = self.context.run_model(
                slug='price.cmf',
                input=token2_instance
            )
            tvl += token2_balance * token2_price['price']
            prices.update({token2_symbol: token2_price['price']})

        # Fetching token3 details if present in thee pool
        if token3 is None:
            pass
        else:
            token3_instance = Token(address=token3)
            token3_name, token3_symbol = token3_instance.name, token3_instance.symbol
            token3_balance = token3_instance.scaled(
                token3_instance.functions.balanceOf(pool).call()
            )
            # Updating number of tokens present
            n += 1
            # Updating pool name
            pool_name = pool_name + '/{}-{}'.format(str(token3_name), str(token3_symbol))
            token3_price = self.context.run_model(
                slug='price.cmf',
                input=token3_instance
            )
            tvl += token3_balance * token3_price['price']
            prices.update({token3_symbol: token3_price['price']})

        # Calculating Volume in 24 Hours

        return PoolVolumeInfo(
            name=pool_name,
            address=Address(pool),
            coin_balances=coin_balances,
            prices=prices,
            tvl=tvl,
            volume24h=volume24h
        )


@Model.describe(slug="contrib.curve-get-tvl-and-volume-historical",
                version="1.0",
                display_name="Curve pool - TVL and Volume Historical",
                description="Runs contrib.curve-get-tvl-and-volume per day",
                input=PoolVolumeInfoHistoricalInput,
                output=dict)
class CurveGetTVLAndVolumeHistorical(Model):
    def run(self, input: PoolVolumeInfoHistoricalInput) -> dict:
        d_start, d_end = input.date_range
        if d_start > d_end:
            d_start, d_end = d_end, d_start

        dt_start = datetime.combine(d_start, datetime.max.time(), tzinfo=timezone.utc)
        dt_end = datetime.combine(d_end, datetime.max.time(), tzinfo=timezone.utc)

        interval = (dt_end - dt_start).days + 1
        window = f'{interval} days'
        interval = '1 day'

        # TODO: add two days to the end as work-around to current start-end-window
        ts_as_of_end_dt = self.context.block_number.from_timestamp(
            ((dt_end + timedelta(days=2)).timestamp())).timestamp

        pool_infos = self.context.historical.run_model_historical(
            model_slug='contrib.curve-get-tvl-and-volume',
            model_input=input.pool_address,
            model_return_type=PoolVolumeInfo,
            window=window,
            interval=interval,
            end_timestamp=ts_as_of_end_dt)

        return {'pool_infos': pool_infos}


@Model.describe(slug="contrib.uni-sushi-get-tvl-and-volume",
                version="1.0",
                display_name="Sushiswap & Uniswap get details for a pool",
                description="Returns the token details of the pool",
                input=Contract,
                output=PoolVolumeInfo)
class UniSushiGetTVLAndVolume(Model):
    def run(self, input: Contract) -> PoolVolumeInfo:
        # Converting to CheckSum Address
        pool = Address(input.address).checksum
        # Pool name
        pool_name = str('None')
        # Dict of coin balances
        coin_balances = {}
        # Dict of prices
        prices = {}
        # Total Value Locked
        tvl = float(0)
        # Volume in Past 24 Hours
        volume24h = float(0)
        # Initiating the contract instance
        pool_contract_instance = Contract(address=pool)

        try:
            pool_contract_instance.abi
        except ModelDataError:
            pool_contract_instance = Contract(address=pool, abi=UNISWAP_V3_POOL_ABI)

        # fetching token adresses of each asset in pool
        token0_instance = Token(address=pool_contract_instance.functions.token0().call())
        token1_instance = Token(address=pool_contract_instance.functions.token1().call())

        # Fetching token0 and token1 details and balance
        token0_name, token0_symbol = token0_instance.name, token0_instance.symbol
        token0_balance = token0_instance.scaled(token0_instance.functions.balanceOf(pool).call())
        coin_balances.update({token0_symbol: token0_balance})
        token0_price = self.context.run_model(
            slug='price.cmf',
            input=token0_instance
        )
        tvl += token0_balance * token0_price['price']
        prices.update({token0_symbol: token0_price['price']})

        token1_name, token1_symbol = token1_instance.name, token1_instance.symbol
        token1_balance = token1_instance.scaled(token1_instance.functions.balanceOf(pool).call())
        coin_balances.update({token1_symbol: token1_balance})
        token1_price = self.context.run_model(
            slug='price.cmf',
            input=token1_instance
        )
        tvl += token1_balance * token1_price['price']
        prices.update({token1_symbol: token1_price['price']})

        # Pool Name
        pool_name = '{}-{}/{}-{}'.format(
            str(token0_name), str(token0_symbol),
            str(token1_name), str(token1_symbol)
        )

        # Calculating Volume in 24 Hours

        return PoolVolumeInfo(
            name=pool_name,
            address=Address(pool),
            coin_balances=coin_balances,
            prices=prices,
            tvl=tvl,
            volume24h=volume24h
        )


@Model.describe(slug="contrib.sushiswap-get-tvl-and-volume",
                version="1.0",
                display_name="Sushiswap get details for a pool",
                description="Returns the token details of the pool",
                input=Contract,
                output=PoolVolumeInfo)
class SushiswapGetTVLAndVolume(Model):
    def run(self, input: Contract) -> PoolVolumeInfo:
        pool_info = self.context.run_model(
            slug='contrib.uni-sushi-get-tvl-and-volume',
            input=input,
            return_type=PoolVolumeInfo)
        pool_info.name = f'Sushiswap : {pool_info.name}'
        return pool_info


@Model.describe(slug="contrib.sushiswap-get-tvl-and-volume-historical",
                version="1.0",
                display_name="Sushiswap TVL and Volume Historical",
                description="Runs contrib.sushiswap-get-tvl-and-volume per day",
                input=PoolVolumeInfoHistoricalInput,
                output=dict)
class SushiswapGetTVLAndVolumeHistorical(Model):
    def run(self, input: PoolVolumeInfoHistoricalInput) -> dict:
        d_start, d_end = input.date_range
        if d_start > d_end:
            d_start, d_end = d_end, d_start

        dt_start = datetime.combine(d_start, datetime.max.time(), tzinfo=timezone.utc)
        dt_end = datetime.combine(d_end, datetime.max.time(), tzinfo=timezone.utc)

        interval = (dt_end - dt_start).days + 1
        window = f'{interval} days'
        interval = '1 day'
        # TODO: add two days to the end as work-around to current start-end-window
        ts_as_of_end_dt = self.context.block_number.from_timestamp(
            ((dt_end + timedelta(days=2)).timestamp())).timestamp
        pool_infos = self.context.historical.run_model_historical(
            model_slug='contrib.sushiswap-get-tvl-and-volume',
            model_input=input.pool_address,
            model_return_type=PoolVolumeInfo,
            window=window,
            interval=interval,
            end_timestamp=ts_as_of_end_dt)

        return {'pool_infos': pool_infos}


@Model.describe(slug="contrib.uniswap-get-tvl-and-volume",
                version="1.0",
                display_name="Uniswap TVL and Volume",
                description="Returns the token details of the pool",
                input=Contract,
                output=PoolVolumeInfo)
class UniswapGetTVLAndVolume(Model):
    def run(self, input: Contract) -> PoolVolumeInfo:
        # Initiating the contract instance
        pool_contract_instance = Contract(address=input.address)
        # Fee
        fee = pool_contract_instance.functions.fee().call()
        # Pool TVL and Volume Info
        pool_info = self.context.run_model(
            slug='contrib.uni-sushi-get-tvl-and-volume',
            input=input,
            return_type=PoolVolumeInfo)
        pool_info.name = f'Uniswap V3 : {pool_info.name}-{fee}'
        return pool_info


@Model.describe(slug="contrib.uniswap-get-tvl-and-volume-historical",
                version="1.0",
                display_name="Uniswap TVL and Volume Historical",
                description="Runs contrib.uniswap-get-tvl-and-volume per day",
                input=PoolVolumeInfoHistoricalInput,
                output=dict)
class UniswapGetTVLAndVolumeHistorical(Model):
    def run(self, input: PoolVolumeInfoHistoricalInput) -> dict:
        d_start, d_end = input.date_range
        if d_start > d_end:
            d_start, d_end = d_end, d_start

        dt_start = datetime.combine(d_start, datetime.max.time(), tzinfo=timezone.utc)
        dt_end = datetime.combine(d_end, datetime.max.time(), tzinfo=timezone.utc)

        interval = (dt_end - dt_start).days + 1
        window = f'{interval} days'
        interval = '1 day'

        # TODO: add two days to the end as work-around to current start-end-window
        ts_as_of_end_dt = self.context.block_number.from_timestamp(
            ((dt_end + timedelta(days=2)).timestamp())).timestamp

        pool_infos = self.context.historical.run_model_historical(
            model_slug='contrib.uniswap-get-tvl-and-volume',
            model_input=input.pool_address,
            model_return_type=PoolVolumeInfo,
            window=window,
            interval=interval,
            end_timestamp=ts_as_of_end_dt)

        return {'pool_infos': pool_infos}
