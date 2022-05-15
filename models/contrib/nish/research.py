from datetime import datetime, timedelta, timezone, date
from typing import Tuple
from credmark.cmf.model import Model
from credmark.cmf.types import (
    Address,
    Contract,
    Token,
)
from credmark.dto import (
    DTO,
)


# Get token balance of an address on ethereum chain
def ethereum_token_balance_of_address(contract_address, account_address):
    '''
            Get token balance of an address method
            Args::
                contract_address: Ethereum Address of the token contract
                account_address: Ethereum Address of account whose token balance is to be fetched
                _apiKey: Etherscan API Key
            Returns::
                _name: Name of token
                _balance: Token Balance of Account
    '''

    contract_address = Address(contract_address).checksum

    _contract = Token(address=contract_address)

    _name = _contract.functions.name().call()
    _balance = _contract.functions.balanceOf(account_address).call()
    _decimals = _contract.functions.decimals().call()
    _symbol = _contract.functions.symbol().call()

    _balance = float(_balance)/pow(10, _decimals)

    return (_name, _symbol, _balance)


# Function to catch naming error while fetching mandatory data
def try_or(func, default=None, expected_exc=(Exception,)):
    try:
        return func()
    except expected_exc:
        return default



class PoolVolumeInfo(Contract):
    name: str
    address: Address
    coin_balances : dict
    prices : dict
    tvl : float
    volume24h : float


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
    def run(self, input) -> PoolVolumeInfo:
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
        token0_name, token0_symbol, token0_balance = ethereum_token_balance_of_address(token0, pool)
        coin_balances.update({token0_symbol : token0_balance})
        token0_price = self.context.run_model(
                                slug = 'token.price',
                                input = Token(address=token0)
                            )
        tvl += token0_balance * token0_price['price']
        prices.update({token0_symbol : token0_price['price']})


        token1_name, token1_symbol, token1_balance = ethereum_token_balance_of_address(token1, pool)
        coin_balances.update({token1_symbol : token1_balance})
        token1_price = self.context.run_model(
                                slug = 'token.price',
                                input = Token(address=token1)
                            )
        tvl += token1_balance * token1_price['price']
        prices.update({token1_symbol : token1_price['price']})

        # Pool Name
        pool_name = 'Curve.fi : {}-{}/{}-{}'.format(
            str(token0_name), str(token0_symbol),
            str(token1_name), str(token1_symbol)
        )

        # Fetching token2 details if present in thee pool
        if token2 is None:
            pass
        else:
            t2_name, t2_symbol, t2_balance = ethereum_token_balance_of_address(token2, pool)
            # Updating coins
            coin_balances.update({t2_symbol : t2_balance})
            # Updating number of tokens present
            n += 1
            # Updating pool name
            pool_name = pool_name + '/{}-{}'.format(str(t2_name),str(t2_symbol))
            t2_price = self.context.run_model(
                                    slug = 'token.price',
                                    input = Token(address=token2)
                                    )
            tvl += t2_balance * t2_price['price']
            prices.update({t2_symbol : t2_price['price']})

        # Fetching token3 details if present in thee pool
        if token3 is None:
            pass
        else:
            t3_name, t3_symbol, t3_balance = ethereum_token_balance_of_address(token3, pool)
            coin_balances.update({t3_symbol : t3_balance})
            # Updating number of tokens present
            n += 1
            # Updating pool name
            pool_name = pool_name + '/{}-{}'.format(str(t3_name),str(t3_symbol))
            t3_price = self.context.run_model(
                                    slug = 'token.price',
                                    input = Token(address=token3)
                                    )
            tvl += t3_balance * t3_price['price']
            prices.update({t3_symbol : t3_price['price']})

        # Calculating Volume in 24 Hours



        return PoolVolumeInfo(
                name = pool_name,
                address = Address(pool),
                coin_balances = coin_balances,
                prices = prices,
                tvl = tvl,
                volume24h = volume24h
        )


@Model.describe(slug="contrib.curve-get-tvl-and-volume-historical",
                version="1.0",
                display_name="Compound pools value history",
                description="Compound pools value history",
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
        # fetching token adresses of each asset in pool
        token0 = Token(address=pool_contract_instance.functions.token0().call())
        token1 = Token(address=pool_contract_instance.functions.token1().call())
        # Fetching token0 and token1 details and balance
        t0_name, t0_symbol, t0_balance = ethereum_token_balance_of_address(token0.address, pool)
        coin_balances.update({t0_symbol : t0_balance})
        t0_price = self.context.run_model(
                                slug = 'token.price',
                                input = Token(address=token0.address)
                            )
        tvl += t0_balance * t0_price['price']
        prices.update({t0_symbol : t0_price['price']})


        t1_name, t1_symbol, t1_balance = ethereum_token_balance_of_address(token1.address, pool)
        coin_balances.update({t1_symbol : t1_balance})
        t1_price = self.context.run_model(
                                slug = 'token.price',
                                input = Token(address=token1.address)
                            )
        tvl += t1_balance * t1_price['price']
        prices.update({t1_symbol : t1_price['price']})

        # Pool Name
        pool_name = '{}-{}/{}-{}'.format(
            str(t0_name), str(t0_symbol),
            str(t1_name), str(t1_symbol)
        )

        # Calculating Volume in 24 Hours

        return PoolVolumeInfo(
                name = pool_name,
                address = Address(pool),
                coin_balances = coin_balances,
                prices = prices,
                tvl = tvl,
                volume24h = volume24h
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
            slug = 'contrib.uni-sushi-get-tvl-and-volume',
            input = input)
        pool_info['name'] = 'Sushiswap : ' + str(pool_info['name'])
        return pool_info


@Model.describe(slug="contrib.sushiswap-get-tvl-and-volume-historical",
                version="1.0",
                display_name="Compound pools value history",
                description="Compound pools value history",
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
                display_name="uniswap get details for a pool",
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
            slug = 'contrib.uni-sushi-get-tvl-and-volume',
            input = input)
        pool_info['name'] = 'Uniswap V3 : '+ str(pool_info['name']) + '-' + str(fee)
        return pool_info

@Model.describe(slug="contrib.uniswap-get-tvl-and-volume-historical",
                version="1.0",
                display_name="Compound pools value history",
                description="Compound pools value history",
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
