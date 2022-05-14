from credmark.cmf.model import Model
from datetime import datetime, timezone
from typing import Tuple
from credmark.dto import (
    DTO,
    DTOField,
)

from credmark.cmf.types import (
    Token,
    Price,
)

import numpy as np
import pandas as pd
import math


class UniswapVarTokenInput(DTO):
    tokens: Tuple[str, str]


class ContractUniswapVarInput(DTO):
    range_percent: int = DTOField(default=5, description="Window Range to use")
    total_amount: int = DTOField(default=10000, description="Total Amount of to use in USD")
    start_date: str = DTOField(description="Starting Date")
    window: int = DTOField(description="no. of days")
    token1: str = DTOField(description="Token 1 Symbol")
    token2: str = DTOField(description="Token 2 Symbol")
    type: str = DTOField(default="V3",
                         description="The version of Uniswap to use for var calculation")


class ContractUniswapVarOutput(DTO):
    date: str = DTOField(description="Total Amount of to use in USD")
    lower_bound_per: str = DTOField(description="Lower Bound Percentile")
    upper_bound_per: str = DTOField(description="upper Bound Percentile")
    lower_bound: str = DTOField(description="Lower Bound")
    upper_bound: str = DTOField(description="upper Bound")
    var: str = DTOField(description="Var")
    var_by_current_position: str = DTOField(description="Var / Current Position")
    impermanent_loss_usd: str = DTOField(description="Impermanent Loss in USD")
    hodl_loss: str = DTOField(description="HODL Loss")
    type_: str = DTOField(description="Uniswap Type")


@Model.describe(slug="finance.uniswapvar",
                version="1.0",
                display_name="UniswapVar",
                description="Var for Uniswap v2 and v3",
                input=ContractUniswapVarInput,
                output=ContractUniswapVarOutput)
class UniswapVar(Model):
    def run(self, input: ContractUniswapVarInput) -> ContractUniswapVarOutput:
        range_per = input.range_percent
        total_amount = input.total_amount
        amount_token1 = total_amount/2
        amount_token2 = total_amount/2
        start_date = input.start_date
        window = input.window+10
        typ = input.type
        end = datetime.strptime(start_date, "%Y-%m-%d")
        model_window = f'{window} days'
        interval = '1 day'
        dt_end = datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc)
        ts_as_of_end_dt = self.context.block_number.from_timestamp(
            ((dt_end).timestamp())).timestamp

        token1 = Token(symbol=input.token1)
        token1_address = token1.address
        token2 = Token(symbol=input.token2)
        token2_address = token2.address

        df = pd.DataFrame()

        token1_prices = []
        token2_prices = []
        dates = []

        prices = self.context.historical.run_model_historical(
            model_slug='token.price',
            model_input=Token(address=token1_address),
            model_return_type=Price,
            window=model_window,
            interval=interval,
            end_timestamp=ts_as_of_end_dt)

        for res in prices.series:
            token1_prices.append(res.output.price)
            dates.append(datetime.fromtimestamp(res.blockTimestamp).strftime("%Y-%m-%d"))

        prices = self.context.historical.run_model_historical(
            model_slug='token.price',
            model_input=Token(address=token2_address),
            model_return_type=Price,
            window=model_window,
            interval=interval,
            end_timestamp=ts_as_of_end_dt)

        for res in prices.series:
            token2_prices.append(res.output.price)

        df['Date'] = pd.Series(dates)

        df['token1/USD'] = pd.Series(token1_prices)

        df['token2/USD'] = pd.Series(token2_prices)
        df = df.sort_values(by='Date', ascending=False).reset_index(drop=True)
        if len(df) == 0 or df.isnull().values.any():
            self.logger.error("Not sufficient data in this Date range")
        window = window-10
        df['token2/token1'] = df['token2/USD']/df['token1/USD']
        df['token1/token2'] = 1/df['token2/token1']
        df['temp_rel_change'] = np.nan
        df['temp_rel_change'][:-10] = df['token1/token2'][10:]
        df['10D_rel_change'] = (df['token1/token2']/df['temp_rel_change'])-1
        df.reset_index(inplace=True)
        df['Obs_N'] = df['index']-10
        df['Lower_Bound'] = df['token1/token2']*(1-(range_per/100))
        df['Upper_Bound'] = df['token1/token2']*(1+(range_per/100))
        lower_price = df['Lower_Bound'][0]
        upper_price = df['Upper_Bound'][0]
        current_price = df['token1/token2'][0]
        df['IL'] = np.nan
        if '2' not in typ:
            var1 = (1+abs(df['10D_rel_change'])).apply(np.sqrt)
            var2 = math.sqrt(lower_price/current_price)
            var3 = math.sqrt(current_price/upper_price)
            df['IL'] = np.nan
            df['IL'] = (2*(var1)/(1+1+abs(df['10D_rel_change']))-1) * \
                (1/(1-(var2+(1+abs(df['10D_rel_change']))*var3)/(1+1+abs(df['10D_rel_change']))))
        else:
            df['IL'] = 2*(((1+df['10D_rel_change'])**1/2))/(1+df['10D_rel_change'])-1
        df['temp_token1/USD_Holding'] = np.nan
        df['temp_token1/USD_Holding'][:-10] = df['token1/USD'][10:]
        df['token1/USD_Holding'] = ((df['token1/USD'] -
                                     df['temp_token1/USD_Holding'])/df['token1/USD'])
        df['temp_token2/USD_Holding'] = np.nan
        df['temp_token2/USD_Holding'][:-10] = df['token2/USD'][10:]
        df['token2/USD_Holding'] = (df['token2/USD']-df['temp_token2/USD_Holding'])/df['token2/USD']
        df['SimdMTM'] = np.nan
        df['SimdMTM_token1'] = amount_token1*(1+df['token2/USD_Holding'])
        df['SimdMTM_token2'] = amount_token2*(1+df['token1/USD_Holding'])
        df['SimdMTM'] = df['SimdMTM_token1']+df['SimdMTM_token2']
        df['UnrealizedPNL'] = df['SimdMTM']-total_amount
        if '2' in typ:
            df['IL_usd'] = df['SimdMTM']*df['IL']
        else:
            df['IL_usd'] = df['SimdMTM']*(df['IL'].apply(lambda x: max(-1, x)))
        df['TotalMTM'] = df['SimdMTM']+df['IL_usd']
        df['Total_PNL'] = df['TotalMTM']-total_amount
        df = df[(df['Obs_N'] >= 1) & (df['Obs_N'] <= window)].reset_index(drop=True)
        index = (1-0.99)*window
        index = math.floor(index)
        df = df.sort_values(by=['Total_PNL']).reset_index(drop=True)
        var_result = df.iloc[index].to_dict()
        var_result['VaR/Current Position'] = (var_result['Total_PNL']/total_amount)*100
        date = str(var_result['Date'])
        lower_bound_per = str(range_per)
        upper_bound_per = str(range_per)
        lower_bound = str(lower_price)
        upper_bound = str(upper_price)
        var = str(abs(var_result['Total_PNL']))
        var_by_current_position = str(abs(var_result['VaR/Current Position']))
        impermanent_loss_usd = str(abs(var_result['IL_usd']))
        hodl_loss = str(abs(var_result['UnrealizedPNL']))
        type_ = str(typ)
        return ContractUniswapVarOutput(
            date=date,
            lower_bound_per=lower_bound_per,
            upper_bound_per=upper_bound_per,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            var=var,
            var_by_current_position=var_by_current_position,
            impermanent_loss_usd=impermanent_loss_usd,
            hodl_loss=hodl_loss,
            type_=type_
        )
