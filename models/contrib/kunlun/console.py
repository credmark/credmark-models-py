# pylint: disable=locally-disabled, unused-import, unused-variable
from typing import List
from datetime import datetime, date, timezone, timedelta
import IPython

import logging
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
    ContractLedger,
)

from credmark.dto import DTO, DTOField, EmptyInput, IterableListGenericDTO, PrivateAttr

from credmark.cmf.types.ledger import (BlockTable, ContractTable,
                                       LogTable,
                                       ReceiptTable, TokenTable,
                                       TokenTransferTable, TraceTable,
                                       TransactionTable)

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
    blocks: List[BlockNumber] = []

    def help(self):
        logging.info('# Pre-defined (shorthand) to Credmark model utilities')
        logging.info('ledger = self.context.ledger')
        logging.info('run_model = self.context.run_model'
                     '(model_slug, input=EmptyInput(), return_type=dict): run a model')
        logging.info(
            'run_model_historical = self.context.historical.run_model_historical'
            '(model_slug, model_input, model_return_type, window, interval, '
            'end_timestamp, snap_clock)')
        logging.info('models = self.context.models')
        logging.info('block_number = self.context.block_number')
        logging.info('chain_id = self.context.chain_id')
        logging.info('web3 = self.context.web3')

        logging.info('# Console functions')
        logging.info('self.where(): where you are in the chain of blocks')
        logging.info('self.save("output_filename"): save console history to {output_filename}.py')
        logging.info('self.load("input_filename"): load and run {input_filename}.py')
        logging.info('self.get_dt(y,m,d,h=0,m=0,s=0,ms=0): create UTC time')
        logging.info('self.get_block(timestamp): get the block number before the timestamp')
        logging.info('self.goto_block(block_number): run the console as of a past block number')

    def where(self):
        logging.info(f'You are {len(self.blocks)} blocks deep.')
        logging.info(f'The block journey is {self.blocks}')

    def save(self, filename):
        ipython = IPython.get_ipython()
        if ipython is not None:
            ipython.magic(f"%save {filename}.py")

    def load(self, filename):
        ipython = IPython.get_ipython()
        if ipython is not None:
            ipython.magic(f"%load {filename}.py")

    # pylint: disable= too-many-arguments
    def get_dt(self, year, month, day, hour=0, minute=0, second=0, microsecond=0):
        return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc)

    def get_block(self, in_dt):
        return BlockNumber.from_timestamp(in_dt.replace(tzinfo=timezone.utc).timestamp())

    def goto_block(self, to_block):
        self.context.run_model(self.slug, block_number=to_block)

    def run(self, _) -> dict:
        self.blocks.append(self.context.block_number)

        ledger = self.context.ledger
        run_model = self.context.run_model
        models = self.context.models
        block_number = self.context.block_number
        chain_id = self.context.chain_id
        web3 = self.context.web3
        run_model_historical = self.context.historical.run_model_historical

        IPython.embed(banner1=(f'Enter CmfConsole on block {self.context.block_number}. '
                               'Help: self.help(), Quit: quit()'),
                      banner2='Available types are BlockNumber, Address, Contract, Token...',
                      exit_msg=f'Exiting the CmfConsol on block {self.context.block_number}. You are left on blocks {self.blocks[:-1]}.'
                      )
        self.blocks.pop()
        return {'block_number': self.context.block_number}
