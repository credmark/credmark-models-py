import math
from datetime import datetime, timedelta, timezone, date
from typing import Tuple
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import (
    Address,
    Contract,
    Token
)
from credmark.dto import (
    DTO
)


# Function to catch naming error while fetching mandatory data
def try_or(func, default=None, expected_exc=(Exception,)):
    try:
        return func()
    except expected_exc:
        return default


class CurvePoolPeggingInfo(Contract):
    name: str
    address: Address
    coin_balances: dict
    A: float
    chi: float
    ratio: float


@Model.describe(slug="contrib.curve-get-pegging-ratio",
                version="1.1",
                display_name="Get pegging ratio for all of Curve's pools",
                description="Get pegging ratio for all of Curve's pools",
                input=Contract,
                output=CurvePoolPeggingInfo)
class CurveGetPeggingRatio(Model):
    def run(self, input: Contract) -> CurvePoolPeggingInfo:
        # Converting to CheckSum Address
        pool = Address(input.address)
        # Pool name
        pool_name = str('None')
        # Dict of coin balances
        coin_balances = {}
        # Amplification Coeffecient A
        a = float(0)
        # Leverage X(chi)
        chi = float(0)
        # Ratio of pegging
        ratio = float(0)
        # Initiating the contract instance
        pool_contract_instance = Contract(address=pool)
        # Fetching A for Pool
        a = pool_contract_instance.functions.A().call()
        # Number of tokens in pool (Initial no. of tokens=2)
        n = 2
        # initiating token counter and fetching balance of each asset in pool
        token0 = pool_contract_instance.functions.coins(0).call()
        token1 = pool_contract_instance.functions.coins(1).call()
        # If third token present
        token2 = try_or(lambda: pool_contract_instance.functions.coins(2).call())
        # If fourth token present
        token3 = try_or(lambda: pool_contract_instance.functions.coins(3).call())
        # Fetching token0 and token1 details
        token0_instance = Token(address=token0)
        token0_name, token0_symbol = token0_instance.name, token0_instance.symbol
        token0_balance = token0_instance.scaled(token0_instance.functions.balanceOf(pool).call())
        coin_balances.update({token0_symbol: token0_balance})

        token1_instance = Token(address=token1)
        token1_name, token1_symbol = token1_instance.name, token1_instance.symbol
        token1_balance = token1_instance.scaled(token1_instance.functions.balanceOf(pool).call())
        coin_balances.update({token1_symbol: token1_balance})

        # Pool Name
        pool_name = 'Curve.fi : {} -{}/ {}-{}'.format(
            str(token0_name), str(token0_symbol), str(token1_name), str(token1_symbol))

        # Calculating D for token0 and token1
        d = token0_balance + token1_balance

        # Product of tokens' quantity for token0 and token1
        product = token0_balance * token1_balance

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
            # Updating quantity product
            product *= token2_balance
            # Updating D
            d += token2_balance
            # Updating pool name
            pool_name = pool_name + '/{}-{}'.format(str(token2_name), str(token2_symbol))

        # Fetching token3 details if present in thee pool
        if token3 is None:
            pass
        else:
            token3_instance = Token(address=token3)
            token3_name, token3_symbol = token3_instance.name, token3_instance.symbol
            token3_balance = token3_instance.scaled(
                token3_instance.functions.balanceOf(pool).call()
            )
            coin_balances.update({token3_symbol: token3_balance})
            # Updating number of tokens present
            n += 1
            # Updating quantity product
            product *= token3_balance
            # Updating D
            d += token3_balance
            # Updating pool name
            pool_name = pool_name + '/{}-{}'.format(str(token3_name), str(token3_symbol))

        # Calculating ratio, this gives information about peg
        ratio = product / pow((d/n), n)

        # Calculating 'chi'
        chi = a * ratio

        return CurvePoolPeggingInfo(
            address=pool,
            name=pool_name,
            coin_balances=coin_balances,
            A=a,
            chi=chi,
            ratio=ratio)


class CurvePoolsValueHistoricalInput(DTO):
    pool: Contract
    date_range: Tuple[date, date]


@Model.describe(slug="contrib.curve-get-pegging-ratio-historical",
                version="1.1",
                display_name="Compound pools value history",
                description="Compound pools value history",
                input=CurvePoolsValueHistoricalInput,
                output=dict)
class CurveV2PoolsValueHistorical(Model):
    def run(self, input: CurvePoolsValueHistoricalInput) -> dict:
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
            model_slug='contrib.curve-get-pegging-ratio',
            model_input=input.pool,
            model_return_type=CurvePoolPeggingInfo,
            window=window,
            interval=interval,
            end_timestamp=ts_as_of_end_dt)

        return {'pool_infos': pool_infos}


class CurveDepeggingAmountInput(DTO):
    pool: Contract
    token: Token
    desired_ratio: float


class CurvePoolDepeggingAmount(DTO):
    pool_info: CurvePoolPeggingInfo
    token: str
    desired_ratio: float
    amount_required: float


@Model.describe(slug="contrib.curve-get-depegging-amount",
                version="1.1",
                display_name="Get pegging ratio for all of Curve's pools",
                description="Get pegging ratio for all of Curve's pools",
                input=CurveDepeggingAmountInput,
                output=CurvePoolDepeggingAmount)
class CurveGetDepeggingAmount(Model):
    def run(self, input: CurveDepeggingAmountInput) -> CurvePoolDepeggingAmount:
        pool_info = self.context.run_model(
            slug='contrib.curve-get-pegging-ratio',
            input=input.pool,
            return_type=CurvePoolPeggingInfo)

        desired_ratio = input.desired_ratio
        coins = list(pool_info.coin_balances.keys())
        n = len(coins)

        token0_balance = pool_info.coin_balances[coins[0]]
        token1_balance = pool_info.coin_balances[coins[1]]

        amount_required = float(0)

        if n == 2:
            if input.token.symbol == coins[0]:
                temp = (2-desired_ratio + 2*math.sqrt(1-desired_ratio))
                amount_token0 = token1_balance * temp / desired_ratio
                amount_required = amount_token0 - token0_balance
            if input.token.symbol == coins[1]:
                temp = (2-desired_ratio + 2*math.sqrt(1-desired_ratio))
                amount_token1 = token0_balance / temp * desired_ratio
                amount_required = amount_token1 - token1_balance
        else:
            raise ModelRunError('Pool with >2 token not implemented.')

        return CurvePoolDepeggingAmount(
            pool_info=pool_info,
            token=input.token.symbol,
            desired_ratio=input.desired_ratio,
            amount_required=amount_required
        )

class CurvePeggingRatioChangeInput(DTO):
    pool: Contract
    amounts: dict

@Model.describe(slug="contrib.curve-get-pegging-ratio-change",
                version="1.0",
                display_name="Get pegging ratio for all of Curve's pools",
                description="Get pegging ratio for all of Curve's pools",
                input=CurvePeggingRatioChangeInput,
                output=CurvePoolPeggingInfo)
class CurveGetPeggingRatioChange(Model):
    def run(self, input: CurvePeggingRatioChangeInput) -> CurvePoolPeggingInfo:
        pool_info = self.context.run_model(
            slug = 'contrib.curve-get-pegging-ratio',
            input = input.pool)

        # Tokens and their current balances as feetched from contract
        coin_balances = pool_info["coin_balances"]
        coins = list(coin_balances.keys())
        n = len(coins)
        # Amount of tokens to be added or removed as fetched from contract
        coins_to_be_changed = list(input.amounts.keys())
        m =  len(coins_to_be_changed)
        # Appending balances of tokens with response to input provided
        for i in range(m):
            coin = coins_to_be_changed[i]
            if coin in coins:
                coin_balances[coin] = coin_balances[coin] + input.amounts[coin]
            else:
                raise ModelRunError('Pool does not contain the input token.')
        # List of new balances
        new_balances = [coin_balances[coin] for coin in coins]
        # New product of token amount
        product = math.prod(new_balances)
        # New sum of token amount
        d = sum(new_balances)
        # Calculating new ratio
        ratio = product / pow((d/n), n)
        # Calculating 'chi'
        chi = pool_info['A'] * ratio

        return CurvePoolPeggingInfo(
            address= pool_info['address'],
            name= pool_info['name'],
            coin_balances= coin_balances,
            A= pool_info['A'],
            chi= chi,
            ratio= ratio)
