from ensurepip import version
from typing import List
import credmark.model

from credmark.types.models.ledger import (
    TransactionTable
)

from credmark.types.dto import (
    DTO,
)

from credmark.types import (
    Address,
    Contract,
    Contracts,
    Token,
    Tokens,
    BlockSeries
)

from models.tmp_abi_lookup import VOTIUM_MERKLE_ABI

@credmark.model.describe(slug='votium-bribe-claim',
                        version='1.0',
                        input=Address)
class BribeClaim(credmark.model.Model):

    def run(self, input: Address) -> dict:
        return