# pylint: disable=locally-disabled, unused-import
import IPython
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from web3.exceptions import ABIFunctionNotFound

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (
    Address,
    Account, Contract, Token,
    Accounts, Contracts, Tokens,
    Portfolio, Position,
    Price, PriceList,
    BlockNumber,
    NativeToken,
    NativePosition,
    TokenPosition,

)
from credmark.dto import DTO, DTOField, EmptyInput, IterableListGenericDTO, PrivateAttr

from credmark.cmf.types.ledger import TokenTransferTable

import models.tmp_abi_lookup as abi_lookup

from models.credmark.protocols.lending.aave.aave_v2 import (
    AaveDebtInfo,
    AaveDebtInfos,
)

from models.credmark.protocols.lending.compound.compound_v2 import (
    CompoundV2PoolInfo,
    CompoundV2PoolValue
)

from models.credmark.protocols.dexes.curve.curve_finance import (
    CurveFiPoolInfo,
    CurveFiPoolInfos,
)

from models.dtos.volume import (
    TradingVolume,
    TokenTradingVolume,
)

from models.dtos.price import (
    PoolPriceInfo,
    PoolPriceInfos,
    PoolPriceAggregatorInput,
)


@Model.describe(slug='contrib.console',
                version='1.0',
                display_name='Console',
                description='REPL for Cmf')
class CmfConsole(Model):
    def goto_block(self, to_block):
        self.context.run_model(self.slug, block_number=to_block)

    def run(self, _) -> dict:
        IPython.embed(banner1=f'Enter CmfConsole on block {self.context.block_number}',
                      banner2='Available types are BlockNumber, Address, Contract, Token...',
                      exit_msg=f'Exiting the CmfConsol on block {self.context.block_number}'
                      )
        return {'block_number': self.context.block_number}
