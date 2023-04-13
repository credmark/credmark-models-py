# pylint: disable=too-many-lines, bare-except, line-too-long, pointless-string-statement

import os
from typing import Optional, List, Any
from datetime import timedelta
from enum import Enum

import pandas as pd

from credmark.cmf.model import Model
from credmark.cmf.model.errors import (ModelDataError, ModelRunError)
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


class TLSInput(Token):
    tx_history_hours: int = DTOField(default=24, description='Transaction Historical Hours')


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


@Model.describe(slug='tls.score',
                version='0.72',
                display_name='Score a token for its legitimacy',
                description='TLS ranges from 10 (highest, legitimate) to 0 (lowest, illegitimate)',
                category='TLS',
                tags=['token'],
                input=TLSInput,
                output=TLSOutput
                )
class TLSScore(Model):
    INFO = True

    @staticmethod
    def score(_address, _name, _symbol, _score, _items):
        return TLSOutput(address=_address,
                         name=_name,
                         symbol=_symbol,
                         score=_score,
                         items=_items)

    def info(self, message):
        self.logger.info(message)

    # pylint: disable=too-many-return-statements
    def run(self, input: TLSInput) -> TLSOutput:
        items = []

        # 1. Currency code
        try:
            fiat_symbol = FiatCurrency(address=input.address).symbol
            items.append(TLSItem.create(f'Fiat currency code {fiat_symbol}', TLSItemImpact.STOP))
            return self.__class__.score(input.address, None, None, None, items)
        except ModelDataError as _err:
            pass

        self.info(f'[{input.address}] Running TLS model')

        # 2. EOA or Account
        if self.context.web3.eth.get_code(input.address.checksum).hex() == '0x':
            items.append(TLSItem.create('Not an EOA', TLSItemImpact.STOP))
            return self.__class__.score(input.address, None, None, None, items)
        else:
            items.append(TLSItem.create('EOA', TLSItemImpact.NEUTRAL))

        self.info(f'[{input.address}] EOA account')

        # 3. ABI/Source code and ERC-20 check
        # 3.1 get token object
        try_eip1967_proxy = get_eip1967_proxy(self.context,
                                              self.logger,
                                              input.address,
                                              False)

        if try_eip1967_proxy is not None:
            contract = try_eip1967_proxy
        else:
            contract = Contract(address=input.address)

        self.info(f'[{input.address}] Got contract object')

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
            return self.__class__.score(input.address, None, None, None, items)

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
            return self.__class__.score(input.address, None, None, None, items)

        # 4. AAVE collateral / debt tokens - Skip because AAVE may discretionary decide to frozen an asset.

        # 5. Check DEX
        # get liquidity data
        try:
            price = self.context.run_model('price.dex', input={'base': token})
            items.append(TLSItem.create(['DEX price', price], TLSItemImpact.POSITIVE))
        except ModelDataError as err:
            if err.data.message.startswith('There is no liquidity'):
                items.append(TLSItem.create(err.data.message, TLSItemImpact.NEGATIVE))
            else:
                raise
        except ModelRunError as err:
            if err.data.message.startswith(f'[{self.context.block_number}] No pool to aggregate for some='):
                items.append(TLSItem.create('Not traded in DEX', TLSItemImpact.NEGATIVE))
            else:
                raise

        addr_maybe = self.context.run_model('token.underlying-maybe',
                                            input={'address': input.address},
                                            return_type=Maybe[Address],
                                            local=True)

        if addr_maybe.just is not None:
            value_token_input = input.dict() | {'address': addr_maybe.just}
            self.info(f'[{input.address}] Running TLS model for underlying token {addr_maybe.just}')
            underlying_token_tls = self.context.run_model(self.slug, input=value_token_input, return_type=TLSOutput)
            items.append(TLSItem.create(['DEX price is taken from the underlying',
                         addr_maybe.just, underlying_token_tls], TLSItemImpact.NEUTRAL))
        else:
            underlying_token_tls = None

        # 4. Transfer records
        current_block_dt = self.context.block_number.timestamp_datetime
        one_day_earlier = current_block_dt - timedelta(hours=input.tx_history_hours)
        one_day_earlier_block = self.context.block_number.from_timestamp(one_day_earlier)

        def _tx_event():
            try:
                df_tx = pd.DataFrame(token.fetch_events(
                    token.events.Transfer,
                    from_block=one_day_earlier_block, to_block=self.context.block_number,
                    contract_address=token.address))
            except ValueError:
                df_tx = pd.DataFrame(token.fetch_events(
                    token.events.Transfer,
                    from_block=one_day_earlier_block, to_block=self.context.block_number,
                    contract_address=token.address,
                    argument_names=['from', 'to', 'value']))
            return df_tx

        def _tx_cache():
            df_tx_fn = f'tmp/df_tx/df_tx_{input.address}_{one_day_earlier_block}_{self.context.block_number}.csv'

            if os.path.isfile(df_tx_fn):
                df_tx = pd.read_pickle(df_tx_fn)
            else:
                df_tx = _tx_event()
                df_tx.to_pickle(df_tx_fn)
            return df_tx

        def _tx_ledger():
            with self.context.ledger.TokenTransfer as q:
                df_tx = q.select(aggregates=[(q.BLOCK_NUMBER.count_(), 'tx_count')],
                                 where=q.TOKEN_ADDRESS.eq(token.address.lower()).and_(
                                     q.BLOCK_NUMBER.ge(one_day_earlier_block)),
                                 bigint_cols=['tx_count']).to_dataframe()
            return df_tx

        # else
        # df_tx = _tx_event()
        # df_tx_count = df_tx.shape[0]

        df_tx = _tx_ledger()
        tx_count = int(df_tx['tx_count'][0])

        tx_period = f'during last {input.tx_history_hours}h ({one_day_earlier_block} to {self.context.block_number}) or ({one_day_earlier} to {current_block_dt})'

        if tx_count == 0:
            items.append(TLSItem.create(f'No transfer during {tx_period}', TLSItemImpact.STOP))
            if underlying_token_tls is not None and underlying_token_tls.score is not None and underlying_token_tls.score < 3.0:
                items.append(TLSItem.create(['Score is overridden by the underlying', 3.0, underlying_token_tls.score],
                                            TLSItemImpact.NEUTRAL))
                return self.__class__.score(input.address, token_name, token_symbol, underlying_token_tls.score, items)
            return self.__class__.score(input.address, token_name, token_symbol, 3.0, items)

        items.append(TLSItem.create(f'{tx_count} transfers during {tx_period}', TLSItemImpact.POSITIVE))
        if underlying_token_tls is not None and underlying_token_tls.score is not None and underlying_token_tls.score < 7.0:
            items.append(TLSItem.create(['Score is overridden by the underlying', 7.0, underlying_token_tls.score],
                                        TLSItemImpact.NEUTRAL))
            return self.__class__.score(input.address, token_name, token_symbol, underlying_token_tls.score, items)
        return self.__class__.score(input.address, token_name, token_symbol, 7.0, items)
