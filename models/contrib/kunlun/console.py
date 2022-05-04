# pylint: disable=locally-disabled, unused-import
import code

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (
    Address, Contract, Token,
    Contracts, Tokens,
    Portfolio, Position,
    Price, PriceList,
    BlockNumber,
)
from credmark.dto import DTO, EmptyInput, IterableListGenericDTO
import models.tmp_abi_lookup as abi_lookup
from web3.exceptions import ABIFunctionNotFound

import IPython


@Model.describe(slug='contrib.console',
                version='1.0',
                display_name='Console',
                description='REPL for Cmf')
class CmfConsole(Model):
    def goto_block(self, to_block):
        self.context.run_model(self.slug, block_number=to_block)

    def run(self, _) -> dict:
        IPython.embed(banner1=f'Enter CmfConsole on block {self.context.block_number}',
                      banner2='Available types are Address, Contract, Token...',
                      exit_msg=f'Exiting the CmfConsol on block {self.context.block_number}'
                      )
        return {'block_number': self.context.block_number}
