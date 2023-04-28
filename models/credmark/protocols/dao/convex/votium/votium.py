# pylint:disable=unused-import
# ruff: noqa: F401

from typing import List

from credmark.cmf.model import Model
from credmark.cmf.types import (Account, Address, Contract, Contracts, Token,
                                Tokens)
from credmark.dto import DTO


@Model.describe(slug='votium.bribe-claim',
                version='1.0',
                input=Account)
class BribeClaim(Model):
    def run(self, input: Account) -> dict:
        return {}
