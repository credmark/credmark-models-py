from credmark.cmf.model import Model
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
from dateutil import relativedelta
from datetime import datetime, timedelta, timezone


class ContractSharpInput(DTO):
    date: str = DTOField(description="Input Date")
    window: int = DTOField(default=365,
                           description="Number of days on which the sharp ratio will be calculated")
    risk_free_rate: float = DTOField(
        default=0.0, description="Risk Rate to use for sharp ratio")
    tokens: list = DTOField(default=100,
                            description="List of tokens for which Shape ratio has to be calulated")


class ContractSharpOutput(DTO):
    sharp_ratios: dict[str, float] = DTOField(
        default={},
        description="Dictionary of Sharp Ratios with token symbol as key and float as value")


@Model.describe(slug="contrib.finance-sharperatiolisttokens",
                version="1.0",
                display_name="sharperatiolisttokens",
                description="Sharpe Ratio of provided list of tokens",
                input=ContractSharpInput,
                output=ContractSharpOutput)
class Sharpe(Model):
    def run(self, input: ContractSharpInput) -> ContractSharpOutput:
        tokens = input.tokens
        window = input.window
        dat = input.date
        risk_free_rate = input.risk_free_rate*100
        result = {}
        end = datetime.strptime(dat, "%d-%m-%Y")
        model_window = f'{str(window+10)} days'
        dt_end = datetime.combine(
            end, datetime.max.time(), tzinfo=timezone.utc)
        ts_as_of_end_dt = self.context.block_number.from_timestamp(
            ((dt_end + timedelta(days=2)).timestamp())).timestamp
        for token in tokens:
            df = pd.DataFrame()
            token_prices = []
            token_address = Token(symbol=token).address
            prices = self.context.historical.run_model_historical(
                model_slug='token.price',
                model_input=Token(address=token_address),
                model_return_type=Price,
                window=model_window,
                interval="1 day",
                end_timestamp=ts_as_of_end_dt)
            dates = []
            for res in prices.series:
                token_prices.append(res.output.price)
                dates.append(datetime.fromtimestamp(
                    res.blockTimestamp).strftime("%Y-%m-%d"))
            df['Price'] = pd.Series(token_prices)
            df['Date'] = pd.Series(dates)
            columns = ['DailyReturn', 'Yearly_return',
                       'Avg6mReturn', 'St_Dev', 'Sharpe_ratio']
            df[columns] = np.nan
            start = datetime.strptime(dat, "%d-%m-%Y")
            start -= relativedelta.relativedelta(days=window-2)
            df['temp_Price'] = np.nan
            df['temp_Price'][1:] = df['Price'][:-1]
            df['DailyReturn'] = ((df['Price']/df['temp_Price'])-1)*100
            df['Yearly_return'] = df['DailyReturn']*np.sqrt(365)
            rolling_windows = df[['Yearly_return']].rolling(181, min_periods=1)
            df[['Avg6mReturn']] = rolling_windows.mean()
            rolling_windows = df[['Avg6mReturn']].rolling(181, min_periods=1)
            df[['St_Dev']] = rolling_windows.std()
            df['Sharpe_ratio'] = (
                df['Avg6mReturn']-risk_free_rate)/df['St_Dev']
            result[token] = df['Sharpe_ratio'][len(df)-2]

        return ContractSharpOutput(sharp_ratios=result)
