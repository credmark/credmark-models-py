# pylint:disable=line-too-long

from datetime import datetime
from typing import List, Optional

from credmark.cmf.model.errors import ModelDataError, ModelInputError, ModelRunError
from credmark.cmf.types import (
    Address,
    BlockNumber,
    MapBlocksOutput,
    Maybe,
    PriceWithQuote,
    Records,
    Token,
)
from credmark.dto import DTO, DTOField
from web3.exceptions import ContractLogicError


class TokenReturn(DTO):
    token_address: Address
    token_symbol: str
    current_amount: float
    current_value: Optional[float]
    token_return: Optional[float]
    transactions: Optional[int] = DTOField(
        description="Number of transactions")


class TokenReturnOutput(DTO):
    token_returns: List[TokenReturn]
    total_current_value: float
    total_return: float

    @classmethod
    def default(cls):
        return cls(token_returns=[], total_current_value=0, total_return=0)


# pylint:disable=too-many-branches
def token_return(_context, _logger, _df, _token_list, quote=None) -> TokenReturnOutput:
    if _token_list == 'cmf':
        token_list = (_context.run_model(
            'token.list', {}, return_type=Records).to_dataframe()
            ['address']
            .values)
    elif _token_list == 'all':
        token_list = None
    else:
        raise ModelInputError(
            'The token_list field in input shall be one of all or cmf (token list from token.list)')

    all_tokens = []

    _block_times = [BlockNumber(blk).timestamp_datetime
                    for blk in _df.block_number.unique().tolist()]

    _logger.info(
        f'{_df.shape[0]} rows, {_df["token_address"].unique().shape[0]} tokens')

    _token_min_block = _df.groupby('token_address')["block_number"].min()

    for tok_address, dfa in _df.groupby('token_address'):
        min_block_number = int(dfa.block_number.min())

        tok = Token(tok_address).as_erc20(set_loaded=True)

        try:
            dfa = dfa.assign(
                value=lambda x, tok=tok: x.value.apply(tok.scaled))
        except ModelDataError:
            _context.logger.info(tok.address)
            if tok.abi is not None and 'decimals' not in tok.abi.functions:
                continue  # skip for ERC-721`
            continue  # also skip for other error
        except ContractLogicError:
            continue

        try:
            tok_symbol = tok.symbol
        except ModelRunError:
            tok_symbol = ''
        except OverflowError:
            tok_symbol = ''
        except Exception as _err:
            _context.logger.info(f'{_err} with {tok} for symbol')
            tok_symbol = ''

        if (token_list is None or
            tok.address.checksum in token_list or
                tok.contract_name in ['UniswapV2Pair', 'Vyper_contract', ]):
            input = {'base': tok}
            if quote is not None:
                input['quote'] = quote
            then_pq = _context.run_model(slug='price.quote-maybe',
                                         input=input,
                                         return_type=Maybe[PriceWithQuote],
                                         block_number=min_block_number)
            if then_pq.just:
                then_price = then_pq.just.price
            else:
                then_price = None
        else:
            then_price = None

        value = None
        block_numbers = []
        past_prices = {}
        if then_price is not None:
            block_numbers = [int(x)
                             for x in dfa.block_number.unique().tolist()]

            dd = datetime.now()
            pp = _context.run_model('price.quote-maybe-blocks',
                                    input={'base': tok,
                                           'quote': quote,
                                           'block_numbers': block_numbers},
                                    return_type=MapBlocksOutput[Maybe[PriceWithQuote]])

            for r in pp.results:
                if r.output is not None and r.output.just is not None:
                    past_prices[r.blockNumber] = r.output.just.price
                else:
                    if tok_address == '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee':
                        # TODO: for price earlier than DEX was created
                        past_prices[r.blockNumber] = 0
                    else:
                        raise ValueError(
                            f'Unable to obtain price for {tok} on block {r.blockNumber} among {pp.results}')

            value = 0

            tt = datetime.now() - dd
            _logger.info((tok_symbol, then_price, tt.seconds,
                          len(block_numbers), tt.seconds / len(block_numbers),
                          min_block_number))
        else:
            _logger.info((tok_symbol, then_price, len(
                block_numbers), 'Skip price'))

        balance = 0
        for _n, r in dfa.iterrows():
            balance += r.value
            if then_price is not None:
                value += -r.value * past_prices[r.block_number]

        if value is not None:
            if balance != 0:
                current_price = _context.run_model(slug='price.quote',
                                                   input={'base': tok, 'quote': quote},
                                                   return_type=PriceWithQuote).price
                current_value = balance * current_price
            else:
                current_value = 0.0

            tok_return = value + current_value
        else:
            tok_return = None
            current_value = None

        all_tokens.append(
            TokenReturn(
                token_address=tok.address,
                token_symbol=tok_symbol,
                current_amount=balance,
                current_value=current_value,
                token_return=tok_return,
                transactions=dfa.shape[0]))

    total_current_value = sum(x.current_value for x in all_tokens
                              if x.current_value is not None)

    total_return = sum(x.token_return for x in all_tokens
                       if x.token_return is not None)

    return TokenReturnOutput(
        # + [native_token_return],
        token_returns=all_tokens,
        # + (native_token_return.current_value if native_token_return.current_value is not None else 0)),
        total_current_value=(total_current_value),
        total_return=total_return)
