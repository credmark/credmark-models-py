from typing import List

from credmark.cmf.model import CachePolicy, Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import Price, PriceWithQuote, Some

from models.credmark.protocols.oracle.band_protocol import PriceSymbolInput, PriceSymbolsInput
from models.dtos.price import PriceInput

PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='No possible feed/routing for token pair')


@Model.describe(slug='price.oracle-band-protocol',
                version='1.0',
                display_name='Token Price - from Oracle',
                description='Get token\'s price from Oracle',
                category='protocol',
                subcategory='band_protocol',
                tags=['price'],
                input=PriceInput,
                output=PriceWithQuote,
                cache=CachePolicy.SKIP,
                errors=PRICE_DATA_ERROR_DESC)
class PriceOracleBandProtocol(Model):
    def run(self, input: PriceInput):
        if not input.base.symbol:
            raise ModelDataError('Symbol not found for base token')
        if not input.quote.symbol:
            raise ModelDataError('Symbol not found for quote token')

        result = self.context.run_model('band.price-by-symbol',
                                        PriceSymbolInput(
                                            base_symbol=input.base.symbol,
                                            quote_symbol=input.quote.symbol
                                        ),
                                        return_type=Price)

        return PriceWithQuote(price=result.price,
                              src=result.src,
                              quoteAddress=input.quote.address)


@Model.describe(slug='price.oracle-band-protocol-multiple',
                version='1.0',
                display_name='Token Price - from Oracle',
                description='Get token\'s price from Oracle',
                category='protocol',
                subcategory='band_protocol',
                tags=['price'],
                input=Some[PriceInput],
                output=Some[PriceWithQuote],
                cache=CachePolicy.SKIP,
                errors=PRICE_DATA_ERROR_DESC)
class PriceOracleBandProtocolMultiple(Model):
    def run(self, input: Some[PriceInput]) -> Some[PriceWithQuote]:
        base_symbols: List[str] = []
        quote_symbols: List[str] = []
        for pair in input:
            if not pair.base.symbol:
                raise ModelDataError(f'Symbol not found for base token {pair.base.address}')
            if not pair.quote.symbol:
                raise ModelDataError(f'Symbol not found for quote token {pair.quote.address}')
            base_symbols.append(pair.base.symbol)
            quote_symbols.append(pair.quote.symbol)

        results = self.context.run_model('band.price-by-symbol-bulk',
                                         PriceSymbolsInput(
                                             base_symbols=base_symbols,
                                             quote_symbols=quote_symbols,
                                         ),
                                         return_type=Some[Price])

        return Some(
            some=[PriceWithQuote(price=result.price,
                                 src=result.src,
                                 quoteAddress=input[idx].quote.address)
                  for idx, result in enumerate(results)]
        )
