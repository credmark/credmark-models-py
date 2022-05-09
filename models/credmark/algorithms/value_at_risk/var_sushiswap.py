from credmark.cmf.model import Model
from credmark.dto import (
    DTO,
    DTOField,
)


import numpy as np
import pandas as pd
import datetime
import math
from dateutil import relativedelta, parser


class ContractSushiswapInput(DTO):
    range_percent: int = DTOField(default=5, description="Window Range to use")
    total_amount: int = DTOField(default=10000, description="Total Amount of to use in USD")
    # date


@Model.describe(slug="finance.sushiswapvar",
                version="1.0",
                display_name="Sushiswap",
                description="Sushiswap",
                input=ContractSushiswapInput,
                output=dict)
class Sushiswap(Model):
    def run(self, input: ContractSushiswapInput) -> dict:
        range_per        = input.range_percent
        total_amount     = input.total_amount
        amount_eth       = input.total_amount/2
        amount_btc       = input.total_amount/2
        df               = pd.DataFrame()
        start            = datetime.datetime.strptime("2020-01-01", "%Y-%m-%d")
        start           -= relativedelta.relativedelta(days=364)
        date_generated   = pd.date_range(start, periods=1000)
        df['Date']       = pd.Series(list(date_generated.strftime("%Y-%m-%d")))
        df['Date']       = pd.to_datetime(df['Date'])
        upper_bound_date = pd.to_datetime("2019-12-31")
        lower_bound_date = pd.to_datetime("2018-12-01")
        df = df[(df.Date >= lower_bound_date)
                & (df.Date <= upper_bound_date)].reset_index(drop=True)
        if len(df) == 0:
            self.logger.error("No data in this Date range")
        np.random.seed(0)
        df['ETH/USD']              = pd.Series(np.random.rand(len(df)))
        np.random.seed(1)
        df['BTC/USD']              = pd.Series(np.random.rand(len(df)))
        df['BTC/ETH']              = df['BTC/USD']/df['ETH/USD']
        df['ETH/BTC']              = 1/df['BTC/ETH']
        df['temp_rel_change']      = np.nan
        df['temp_rel_change'][10:] = df['BTC/ETH'][:-10]
        df['10D_rel_change']       = (df['BTC/ETH']/df['temp_rel_change'])-1
        df.reset_index(inplace=True)
        df['Obs_N']                = df['index']-10
        df['Lower_Bound']          = df['BTC/ETH']*(1-(range_per/100))
        df['Upper_Bound']          = df['BTC/ETH']*(1+(range_per/100))
        lower_price                = df['Lower_Bound'][0]
        upper_price                = df['Upper_Bound'][0]
        current_price              = df['BTC/ETH'][0]
        df['IL']                   = np.nan
        var1                       = abs(df['10D_rel_change'])
        var2                       = math.sqrt(lower_price/current_price)
        var3                       = math.sqrt(current_price/upper_price)
        df['IL']                   = (2*((1+var1)**1/2)/(1+1+var1)-1)*(1/(1-(var2+(1+var1)*var3)/(1+1+var1)))
        # else:
        #     df['IL'] = 2*(((1+df['10D_rel_change'])**1/2))/(1+df['10D_rel_change'])-1

        df['temp_ETH/USD_Holding']       = np.nan
        df['temp_ETH/USD_Holding'][:-10] = df['ETH/USD'][10:]
        df['ETH/USD_Holding']            = ((df['ETH/USD']-df['temp_ETH/USD_Holding'])/df['ETH/USD'])
        df['temp_BTC/USD_Holding']       = np.nan
        df['temp_BTC/USD_Holding'][:-10] = df['BTC/USD'][10:]
        df['BTC/USD_Holding']            = (df['BTC/USD']-df['temp_BTC/USD_Holding'])/df['BTC/USD']
        df['SimdMTM']                    = np.nan
        df['SimdMTM']                    = amount_btc*(1+df['ETH/USD_Holding'])+amount_eth*(1+df['BTC/USD_Holding'])
        df['UnrealizedPNL']              = df['SimdMTM']-total_amount

        df['IL_usd']                     = df['SimdMTM']*df['IL']
        df['TotalMTM']                   = df['SimdMTM']+df['IL_usd']
        df['Total_PNL']                  = df['TotalMTM']-total_amount
        df                               = df[(df['Obs_N'] >= 1) & (df['Obs_N'] <= 365)].reset_index(drop=True)
        index                  = (1-0.99)*365
        index                  = math.floor(index)
        df                     = df.sort_values(by=['Total_PNL']).reset_index(drop=True)
        var_result             = df.iloc[index].to_dict()
        var_result['VaR/Current Position']            = (var_result['Total_PNL']/total_amount)*100
        result                 = {}
        result['Date']         = str(var_result['Date'])
        result['Lower_Bound%'] = str(range_per)
        result['Upper_Bound%'] = str(range_per)
        result['Lower_Bound']  = str(lower_price)
        result['Upper_Bound']  = str(upper_price)
        result['VaR']          = str(var_result['Total_PNL'])
        result['VaR/Current Position'] = str(var_result['VaR/Current Position'])
        result['Impermanent_Loss_usd'] = str(var_result['IL_usd'])
        result['HODL_Loss']            = str(var_result['UnrealizedPNL'])
        return result
