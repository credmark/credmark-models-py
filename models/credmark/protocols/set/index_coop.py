# pylint: disable=line-too-long, pointless-string-statement

"""
Calculate fees for Index Coop products

DPI
- 0x1494ca1f11d487c2bbe4543e90080aeba4ba3c2b
- 0.95% = 70% Index Coop, 30% DeFi Pulse

MVI:
- setv2_BasicIssuanceModule
- 0x72e364f2abdc788b7e918bc238b21f109cd634d7
- 0.95% = 100% Index Coop

DATA:
- setv2_BasicIssuanceModule
- 0x33d63ba1e57e54779f7ddaeaa7109349344cf5f1
- 0.95% = 70% Index Coop, 30% DeFi Pulse

BED:
- setv2_BasicIssuanceModule
- 0x2af1df3ab0ab157e1e2ad8f88a7d04fbea0c7dc6
- 0.25% = 50% Index Coop, 50% Bankless

GMI:
- setv2_BasicIssuanceModule???
- 0x47110d43175f7f2c2425e7d15792acc5817eb44f
- 1.95% = 60% Index Coop, 40% Bankless

ETH2x-FLI:
- Debt
- 0xaa6e8127831c9de45ae56bb1b0d4d4da6e5665bd
- Streaming Fee: 1.95% (60% Index Coop, 40% DeFi Pulse)
- Mint/Redeem Fee: 0.1% (60% Index Coop, 40% DeFi Pulse)

BTC2x-FLI: Debt
- 0x0b498ff89709d3838a063f1dfa463091f9801c2b'
- Streaming Fee: 1.95% (60% Index Coop, 40% DeFi Pulse)
- Mint/Redeem Fee: 0.1% (60% Index Coop, 40% DeFi Pulse)
"""

from datetime import datetime, timedelta, timezone
from enum import Enum

import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Address, BlockNumber, Contract, Network, Records, Token
from credmark.dto import DTOField

from models.credmark.protocols.set.setv2 import SetV2ModulesOutput, setv2_fee


def index_coop_revenue_issue(
        _logger, _context, _prod_token, _setv2_mod,
        _start_block, _end_block,
        _use_last_price, _streaming_rate, _coop_rate, _mint_redeem_rate=0.0, _coop_mr_rate=0.0):
    """
    This function calculates revenue per day. It will count per day interval

    @params:
    _start_block: start of period (time 0)
    _end_block: end of period (time 1)

    # test

    df_dpi = index_coop_revenue_issue('0x1494ca1f11d487c2bbe4543e90080aeba4ba3c2b',
                                    self.logger, self.context, setv2_BasicIssuanceModule, year, month, 0.0095, 0.7)
    df_mvi = index_coop_revenue_issue('0x72e364f2abdc788b7e918bc238b21f109cd634d7',
                                    self.logger, self.context, setv2_BasicIssuanceModule, year, month, 0.0095, 1.0)
    df_data = index_coop_revenue_issue('0x33d63ba1e57e54779f7ddaeaa7109349344cf5f1',
                                    self.logger, self.context, setv2_BasicIssuanceModule, year, month, 0.0095, 0.7)
    df_bed = index_coop_revenue_issue('0x2af1df3ab0ab157e1e2ad8f88a7d04fbea0c7dc6',
                                    self.logger, self.context, setv2_BasicIssuanceModule, year, month, 0.0025, 0.5)
    df_gmi = index_coop_revenue_issue('0x47110d43175f7f2c2425e7d15792acc5817eb44f',
                                    self.logger, self.context, setv2_BasicIssuanceModule, year, month, 0.0195, 0.6)

    df_eth2x = index_coop_revenue_issue('0xaa6e8127831c9de45ae56bb1b0d4d4da6e5665bd',
                                        self.logger, self.context, setv2_DebtIssuanceModule, year, month, 0.0195, 0.6, 0.001, 0.6)
    df_btc2x = index_coop_revenue_issue('0x0b498ff89709d3838a063f1dfa463091f9801c2b',
                                        self.logger, self.context, setv2_DebtIssuanceModule, year, month, 0.0195, 0.6, 0.001, 0.6)
    """

    token_addr = _prod_token.address
    prod_token_decimals = _prod_token.decimals

    _start_dt = BlockNumber(_start_block).timestamp_datetime
    _end_dt = BlockNumber(_end_block).timestamp_datetime
    period = _end_dt - _start_dt
    days_in_period = period.days
    seconds_in_period = period.seconds
    if seconds_in_period > 0:
        days_in_period += 1

    # To fetch all mint/burn data
    df = setv2_fee(_context, _setv2_mod, 0, _end_block, token_addr)

    # Used previous AUM
    _prev_aum = df.query('blockNumber <= @_start_block')['_quantity'].sum()

    # Used in df.query below, subtract 1 as we use > below.
    _prev_end_block = _start_block - 1

    row_data = []

    for day in range(0, days_in_period):
        new_dt = _start_dt + timedelta(days=day)
        new_dt = datetime(new_dt.year, new_dt.month,
                          new_dt.day, 23, 59, 59, tzinfo=timezone.utc)
        blk_eod = BlockNumber.from_timestamp(new_dt)
        blk_eod, new_dt = (blk_eod, new_dt) if blk_eod < _end_block else (
            _end_block, _end_dt)

        _logger.info(f'{new_dt} at {blk_eod} till {_end_block}')

        unit = df.query(
            'blockNumber <= @blk_eod')['_quantity'].sum() / 10 ** prod_token_decimals
        mint_redeem_events = df.query(
            '(blockNumber > @_prev_end_block) & (blockNumber <= @blk_eod)')['_quantity'] / 10 ** prod_token_decimals
        mint_unit = mint_redeem_events.loc[mint_redeem_events > 0].sum()
        redeem_unit = mint_redeem_events.loc[mint_redeem_events < 0].sum()
        mint_redeem_unit = mint_unit - redeem_unit

        if not _use_last_price:
            try:
                price = _context.run_model(
                    'price.dex', input={'base': _prod_token.address}, block_number=blk_eod)['price']
            except (ModelDataError, ModelRunError):
                price = 1
        else:
            price = 1

        aum = unit * price

        streaming_fee = aum * _streaming_rate / 365
        # Fee to Coop
        streaming_fee_coop = streaming_fee * _coop_rate
        # Fee to methodologist
        streaming_fee_methodologist = streaming_fee * (1 - _coop_rate)

        mint_redeem_fee = mint_redeem_unit * price * _mint_redeem_rate
        # Fee to Coop
        mint_redeem_fee_coop = mint_redeem_fee * _coop_mr_rate
        # Fee to methodologist
        mint_redeem_fee_methodologist = mint_redeem_fee * (1 - _coop_mr_rate)

        prev_start_dt = BlockNumber(_prev_end_block + 1).timestamp_datetime
        row_data.append((_prev_end_block + 1, blk_eod, prev_start_dt, new_dt,
                         mint_unit, redeem_unit, mint_redeem_unit, unit,
                         price, aum,
                         streaming_fee, streaming_fee_coop, streaming_fee_methodologist,
                         mint_redeem_fee, mint_redeem_fee_coop, mint_redeem_fee_methodologist))
        _prev_end_block = blk_eod

    df_fee = pd.DataFrame(
        row_data,
        columns=[
            'start_block_number', 'end_block_number', 'start_datetime', 'end_datetime',
            'mint_unit', 'redeem_unit', 'mint_redeem_unit', 'total_unit',
            'price', 'aum',
            'streaming_fee', 'streaming_fee_coop', 'streaming_fee_methodologist',
            'mint_redeem_fee', 'mint_redeem_fee_coop', 'mint_redeem_fee_methodologist'])

    if _use_last_price:
        try:
            end_price = _context.run_model(
                'price.dex', input={'base': _prod_token.address}, block_number=_end_block)['price']
        except (ModelDataError, ModelRunError):
            end_price = 1

        df_fee = df_fee.assign(
            price=lambda r, p=end_price: r.price * p,
            streaming_fee=lambda r, p=end_price: r.streaming_fee * p,
            streaming_fee_coop=lambda r, p=end_price: r.streaming_fee_coop * p,
            streaming_fee_methodologist=lambda r, p=end_price: r.streaming_fee_methodologist * p,
            mint_redeem_fee=lambda r, p=end_price: r.mint_redeem_fee * p,
            mint_redeem_fee_coop=lambda r, p=end_price: r.mint_redeem_fee_coop * p,
            mint_redeem_fee_methodologist=lambda r, p=end_price: r.mint_redeem_fee_methodologist * p,
        )

    return df_fee


class IndexCoopProductType(str, Enum):
    BASIC = 'basic'
    DEBT = 'debt'


class IndexCoopFee(Contract):
    # product's address is inherited from Contract
    streaming_rate: float = DTOField(description='Streaming fee rate')
    coop_streaming_rate: float = DTOField(
        description='Coop\'s share in streaming fee')
    mint_redeem_rate: float = DTOField(description='Mint and redeem fee rate')
    coop_mint_redeem_rate: float = DTOField(
        description='Coop\'s share in Mint and redeem')
    use_last_price: bool = DTOField(
        False, description='Use end_block\'s price (true) or every block\'s price (false, default)')


class IndexCoopFeeMonthInput(IndexCoopFee):
    year: int
    month: int

    class Config:
        schema_extra = {
            'example': {"address": "0x1494ca1f11d487c2bbe4543e90080aeba4ba3c2b", "streaming_rate": 0.0095,
                        "coop_streaming_rate": 0.7, "mint_redeem_rate": 0, "coop_mint_redeem_rate": 0,
                        "use_last_price": True, "year": 2022, "month": 9,
                        '_test_multi': {'chain_id': 1, 'block_number': 16_000_000}},
            'test_multi': True
        }


class IndexCoopFeeInput(IndexCoopFee):
    start_block: BlockNumber


@Model.describe(slug='indexcoop.fee-month',
                version='0.3',
                display_name='Index Coop Product - Streaming fee',
                description='calculate fee collected from Index Coop\'s products, from AUM and Mint/Burn',
                category='protocol',
                subcategory='set-v2',
                input=IndexCoopFeeMonthInput,
                output=dict)
class IndexCoopFeeMonth(Model):
    def run(self, input: IndexCoopFeeMonthInput):
        _year = input.year
        _month = input.month
        days_in_month = pd.Timestamp(
            year=_year, month=_month, day=1).days_in_month
        prev_eom = datetime(_year, _month, 1, 23, 59, 59,
                            tzinfo=timezone.utc) - timedelta(days=1)
        this_eom = datetime(_year, _month, days_in_month,
                            23, 59, 59, tzinfo=timezone.utc)
        start_block = BlockNumber.from_timestamp(prev_eom)+1
        end_block = BlockNumber.from_timestamp(this_eom)

        fee_model_input = IndexCoopFeeInput(
            address=input.address,
            start_block=start_block,
            streaming_rate=input.streaming_rate,
            coop_streaming_rate=input.coop_streaming_rate,
            mint_redeem_rate=input.mint_redeem_rate,
            coop_mint_redeem_rate=input.coop_mint_redeem_rate,
            use_last_price=input.use_last_price,
        )

        return self.context.run_model(
            'indexcoop.fee',
            input=fee_model_input,
            block_number=end_block)


class IndexCoopStreamingFeeInput(Contract):
    # The product's address is part of the Contract
    start_block: BlockNumber
    streaming_rate: float = DTOField(description='Streaming fee rate')
    coop_streaming_rate: float = DTOField(
        description='Coop\'s share in streaming fee')
    mint_redeem_rate: float = DTOField(description='Mint and redeem fee rate')
    coop_mint_redeem_rate: float = DTOField(
        description='Coop\'s share in Mint and redeem')
    use_last_price: bool = DTOField(
        False, description='Use end_block\'s price (true) or every block\'s price (false, default)')

    class Config:
        schema_extra = {
            'example': {"address": "0x1494ca1f11d487c2bbe4543e90080aeba4ba3c2b", "streaming_rate": 0.0095,
                        "coop_streaming_rate": 0.7, "mint_redeem_rate": 0, "coop_mint_redeem_rate": 0,
                        "use_last_price": True, "start_block": 15_449_618,
                        '_test_multi': {'chain_id': 1, 'block_number': 15_649_594}},
            'test_multi': True
        }


@Model.describe(slug='indexcoop.fee',
                version='0.6',
                display_name='Index Coop Product - Streaming fee',
                description='calculate fee collected from Index Coop\'s products, from AUM and Mint/Burn',
                category='protocol',
                subcategory='set-v2',
                input=IndexCoopStreamingFeeInput,
                output=Records)
class IndexCoopStreamingFee(Model):
    PRODUCT_CONFIG = {
        Network.Mainnet: {
            Address('0x1494ca1f11d487c2bbe4543e90080aeba4ba3c2b'): IndexCoopProductType.BASIC,
            Address('0x72e364f2abdc788b7e918bc238b21f109cd634d7'): IndexCoopProductType.BASIC,
            Address('0x33d63ba1e57e54779f7ddaeaa7109349344cf5f1'): IndexCoopProductType.BASIC,
            Address('0x2af1df3ab0ab157e1e2ad8f88a7d04fbea0c7dc6'): IndexCoopProductType.BASIC,
            Address('0x47110d43175f7f2c2425e7d15792acc5817eb44f'): IndexCoopProductType.BASIC,
            Address('0xaa6e8127831c9de45ae56bb1b0d4d4da6e5665bd'): IndexCoopProductType.DEBT,
            Address('0x0b498ff89709d3838a063f1dfa463091f9801c2b'): IndexCoopProductType.DEBT,
        }
    }

    def run(self, input: IndexCoopStreamingFeeInput):
        setv2_modules = self.context.run_model(
            'set-v2.modules', {}, return_type=SetV2ModulesOutput)
        product_type = self.PRODUCT_CONFIG[self.context.network][input.address]

        if input.start_block >= self.context.block_number:
            raise ModelDataError(
                f'{input.start_block=} needs to be smaller than {self.context.block_number}')

        if product_type == IndexCoopProductType.BASIC:
            setv2_module = setv2_modules.basic_issuance
        elif product_type == IndexCoopProductType.DEBT:
            setv2_module = setv2_modules.debt_issuance
        else:
            raise ModelDataError(
                f'Input contract {input.address} is not an Index Coop product')

        prod_token = Token(input.address)

        df_fee = index_coop_revenue_issue(
            self.logger,
            self.context,
            prod_token,
            setv2_module,
            int(input.start_block),
            int(self.context.block_number),
            _use_last_price=input.use_last_price,
            _streaming_rate=input.streaming_rate,
            _coop_rate=input.coop_streaming_rate,
            _mint_redeem_rate=input.mint_redeem_rate,
            _coop_mr_rate=input.coop_mint_redeem_rate)

        streaming_fees = df_fee.streaming_fee.sum(), df_fee.streaming_fee_coop.sum(
        ), df_fee.streaming_fee_methodologist.sum()
        mint_redeem_fees = df_fee.mint_redeem_fee.sum(
        ), df_fee.mint_redeem_fee_coop.sum(), df_fee.mint_redeem_fee_methodologist.sum()

        self.logger.info(
            f'Total Fee: {streaming_fees[0]+mint_redeem_fees[0]} = {streaming_fees[1]+mint_redeem_fees[1]} + {streaming_fees[2]+mint_redeem_fees[2]}, '
            f'Streaming Fee: {streaming_fees[0]} = {streaming_fees[1]} + {streaming_fees[2]}'
            f'Mint/Redeem fee: {mint_redeem_fees[0]} = {mint_redeem_fees[1]} + {mint_redeem_fees[2]}')

        return Records.from_dataframe(df_fee)
