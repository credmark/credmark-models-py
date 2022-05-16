from typing import (
    List,
)

from credmark.cmf.model import Model
from credmark.dto import (
    DTO,
    DTOField,
)


import pandas as pd
import numpy as np
import random


class ContractMinriskInput(DTO):
    token_symbols: List[str] = DTOField(default=[], description="List of token symbols")
    date: str = DTOField(description="Input Date")


class ContractMinriskOutput(DTO):
    minimum_risk: float = DTOField(default=0.0, description='Minimum Risk Free Rate')


@Model.describe(slug="contrib.finance-minrisk",
                version="1.0",
                display_name="MinRisk",
                description="MinRisk for input tokens",
                input=ContractMinriskInput,
                output=ContractMinriskOutput)
class Minrisk(Model):
    def run(self, input: ContractMinriskInput) -> ContractMinriskOutput:
        tokens = input.token_symbols
        dat = input.date
        names = ['Aave', 'Compound']
        num = int(''.join(dat.split('-'))) % (2**32)
        np.random.seed(num)
        random.seed(10)
        arr = np.random.rand(len(tokens), len(names)+1)
        df = pd.DataFrame(arr, columns=names+['On-chain Volume, in USD bln.'])
        df['On-chain Volume, in USD bln.'] *= 100
        tvls = {}
        tvls['Aave'] = random.random()*10
        random.seed(10)
        tvls['Compound'] = random.random()*10

        def func(col, tvls):
            ans = 0
            prod_tvls = 0
            prod_tvls = float(tvls['Aave'])+float(tvls['Compound'])
            aave = (float(col['Aave'])*float(tvls['Aave']))
            compound = (float(col['Compound'])*float(tvls['Compound']))
            ans = (aave+compound)/prod_tvls
            return ans
        df['Weighted Yield'] = df.apply(lambda col: func(col, tvls), axis=1)
        weightedYield_Volume = ((df['Weighted Yield']*df['On-chain Volume, in USD bln.']).sum())
        volume_sum = (df['On-chain Volume, in USD bln.'].sum())
        minimum_risk_free_rate = weightedYield_Volume/volume_sum
        result = ContractMinriskOutput(minimum_risk=minimum_risk_free_rate)
        return result
