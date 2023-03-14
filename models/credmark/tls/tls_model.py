# pylint: disable=too-many-lines, bare-except, line-too-long, pointless-string-statement

import os
from typing import Optional, List, Any
from datetime import timedelta
from enum import Enum

import pandas as pd

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import (Account, FiatCurrency, Address, Contract,
                                Maybe, Token)
from credmark.dto import (DTO, DTOField)

from models.credmark.tokens.token import get_eip1967_proxy


# pylint:disable=invalid-name
class TLSItemImpact(str, Enum):
    STOP = '!'
    POSITIVE = '+'
    NEGATIVE = '-'
    NEUTRAL = '0'

    @classmethod
    def explain(cls):
        return ', '.join(
            [f'{cls.STOP}: slashing',
             f'{cls.POSITIVE}: positive',
             f'{cls.NEGATIVE}: negative',
             f'{cls.NEUTRAL}: neutral'])


class TLSItem(DTO):
    name: Any
    impact: TLSItemImpact = DTOField(description=TLSItemImpact.explain())

    @classmethod
    def create(cls, _name, _impact):
        return cls(name=_name, impact=_impact)

    class Config:
        use_enum_values = True


class TLSOutput(Account):
    name: Optional[str] = DTOField(description='Name of the token')
    symbol: Optional[str] = DTOField(description='Symbol of the token')
    score: Optional[float] = DTOField(ge=0, le=10, description='Score')
    items: List[TLSItem] = DTOField(description='Score components')

    class Config:
        schema_extra = {
            'examples': [
                {'address': '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9',
                 'name': 'Aave Token',
                 'symbol': 'AAVE',
                 'score': 8.0,
                 'items': []}]
        }


"""
credmark-dev run tls.score -i '{"address":"0x0000000000000000000000000000000000000348"}' # fiat
credmark-dev run tls.score -i '{"address":"0x0000000000000000000000000000000000000349"}' # not an EOA
credmark-dev run tls.score -i '{"address":"0x208A9C9D8E1d33a4f5b371Bf1864AA125379Ba1B"}' # no ABI

credmark-dev run tls.score -i '{"address":"0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B"}' # Unitroller

credmark-dev run tls.score -i '{"address":"0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}'

# Proxy

# cToken
cETH
0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5

aWETH
0x030bA81f1c18d280636F32af80b9AAd02Cf0854e

# RASCAL INU
0x8a3fd50433b28e47ea5f78dabd5749965e795ff6

"""


@Model.describe(
    slug='tls.score',
    version='0.56',
    display_name='Score a token for its legitimacy',
    description='TLS ranges from 10 (highest, legitimate) to 0 (lowest, illegitimate)',
    category='TLS',
    tags=['token'],
    input=Token,
    output=TLSOutput
)
class TLSScore(Model):
    def score(self, _address, _name, _symbol, _score, _items):
        return TLSOutput(address=_address,
                         name=_name,
                         symbol=_symbol,
                         score=_score,
                         items=_items)

    def run(self, input: Token) -> TLSOutput:
        items = []

        # 1. Currency code
        try:
            fiat_symbol = FiatCurrency(address=input.address).symbol
            items.append(TLSItem.create(f'Fiat currency code {fiat_symbol}', TLSItemImpact.STOP))
            return self.score(input.address, None, None, None, items)
        except ModelDataError as _err:
            pass

        # 2. EOA or Account
        if self.context.web3.eth.get_code(input.address.checksum).hex() == '0x':
            items.append(TLSItem.create('Not an EOA', TLSItemImpact.STOP))
            return self.score(input.address, None, None, None, items)
        else:
            items.append(TLSItem.create('EOA', TLSItemImpact.NEUTRAL))

        # 3. ABI/Source code and ERC-20 check
        # 3.1 get token object
        try_eip1967_proxy = get_eip1967_proxy(self.context,
                                              self.logger,
                                              input.address,
                                              False)
        if try_eip1967_proxy is not None:
            contract = try_eip1967_proxy
        else:
            addr_maybe = self.context.run_model('token.underlying-maybe',
                                                input={'address': input.address},
                                                return_type=Maybe[Address],
                                                local=True)
            if addr_maybe.just is not None:
                return self.context.run_model(self.slug, input=input, return_type=TLSOutput)
            else:
                contract = Contract(address=input.address)

        # 3.2 check contract object is an ERC-20
        # 3.2.1 Get ABI inside the token object
        try:
            if contract.proxy_for is not None:
                _ = contract.proxy_for.abi
                items.append(TLSItem.create('Proxy contract', TLSItemImpact.NEUTRAL))
            else:
                _ = contract.abi
                items.append(TLSItem.create('Not a proxy contract', TLSItemImpact.NEUTRAL))
            items.append(TLSItem.create('Found ABI from EtherScan', TLSItemImpact.POSITIVE))
        except ModelDataError:
            items.append(TLSItem.create('No ABI from EtherScan', TLSItemImpact.STOP))
            return self.score(input.address, None, None, None, items)

        # 3.2.2 Is it ERC-20 Token?
        try:
            token = Token(address=input.address)
            token_name = token.name
            token_symbol = token.symbol
            _token_decimals = token.decimals
            _token_total_supply = token.total_supply
            _ = token.functions.balanceOf
            _ = token.functions.transfer
            _ = token.functions.transferFrom
            _ = token.functions.approve
            _ = token.functions.allowance
            _ = token.events.Transfer
            _ = token.events.Approval
            items.append(TLSItem.create('ERC20 Token', TLSItemImpact.NEUTRAL))
        except:
            items.append(TLSItem.create('Not an ERC20 Token', TLSItemImpact.STOP))
            return self.score(input.address, None, None, None, items)

        # 4. AAVE collateral / debt tokens - Skip because AAVE may discretionary decide to frozen an asset.

        # 5. Check DEX
        # get liquidity data
        try:
            price = self.context.run_model('price.dex-db-prefer', input=token)
            items.append(TLSItem.create(['DEX price', price], TLSItemImpact.POSITIVE))
        except ModelDataError as err:
            if err.data.message.startswith('There is no liquidity in'):
                items.append(TLSItem.create(err.data.message, TLSItemImpact.STOP))
            else:
                raise

        # 4. Transfer records
        current_block_dt = self.context.block_number.timestamp_datetime
        one_day_earlier = current_block_dt - timedelta(hours=12)
        one_day_earlier_block = self.context.block_number.from_timestamp(one_day_earlier)

        df_tx_fn = f'tmp/df_tx/df_tx_{input.address}_{one_day_earlier_block}_{self.context.block_number}.csv'

        if os.path.isfile(df_tx_fn):
            df_tx = pd.read_pickle(df_tx_fn)
        else:
            df_tx = pd.DataFrame(token.fetch_events(
                token.events.Transfer,
                from_block=one_day_earlier_block, to_block=self.context.block_number,
                contract_address=token.address))
            df_tx.to_pickle(df_tx_fn)

        tx_period = f'during last 12h ({one_day_earlier_block} to {self.context.block_number}) or ({one_day_earlier} to {current_block_dt})'

        if df_tx.empty:
            items.append(TLSItem.create(f'No transfer during {tx_period}', TLSItemImpact.STOP))
            return self.score(input.address, token_name, token_symbol, 3.0, items)

        items.append(TLSItem.create(f'{df_tx.shape[0]} transfers during {tx_period}', TLSItemImpact.POSITIVE))
        return self.score(input.address, token_name, token_symbol, 7.0, items)
