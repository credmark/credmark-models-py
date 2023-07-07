from typing import List

from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError, ModelEngineError
from credmark.cmf.types import Contract, Network, NetworkDict, Price, Some
from credmark.dto import DTO, DTOField

from models.tmp_abi_lookup import BAND_PROTOCOL_ABI

PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='No possible feed/routing for token pair')

BAND_CONTRACTS = NetworkDict(str, {
    Network.Avalanche: '0x75B01902D9297fD381bcF3B155a8cEAC78F5A35E',
    Network.BSC: '0xDA7a001b254CD22e46d3eAB04d937489c93174C3',
    Network.Mainnet: '0xDA7a001b254CD22e46d3eAB04d937489c93174C3',
    Network.Fantom: '0xDA7a001b254CD22e46d3eAB04d937489c93174C3',
    Network.Optimism: '0xDA7a001b254CD22e46d3eAB04d937489c93174C3',
})


class PriceSymbolInput(DTO):
    base_symbol: str = DTOField(..., description="Base token symbol")
    quote_symbol: str = DTOField('USD', description="Quote token symbol")


@Model.describe(slug='band.price-by-symbol',
                version='1.0',
                display_name='Token Price - from Oracle',
                description='Get token\'s price from Oracle',
                category='protocol',
                subcategory='band_protocol',
                tags=['price'],
                input=PriceSymbolInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class BandProtocolPrice(Model):
    def run(self, input: PriceSymbolInput):
        if self.context.network not in BAND_CONTRACTS:
            raise ModelDataError('Chain not supported')

        contract = Contract(BAND_CONTRACTS[self.context.network])
        try:
            _ = contract.abi
        except (ModelDataError, ModelEngineError):
            contract = contract.set_abi(BAND_PROTOCOL_ABI, set_loaded=True)

        try:
            (rate, lastUpdatedBase, lastUpdatedQuote) = contract.functions.getReferenceData(
                input.base_symbol, input.quote_symbol).call()
            return Price(price=rate/10**18,
                         src=f'{self.slug}|b:{lastUpdatedBase}|q:{lastUpdatedQuote}')
        except Exception as err:  # ruff: noqa: E722
            raise ModelDataError('No possible feed/routing for one of the token pairs') from err


class PriceSymbolsInput(DTO):
    base_symbols: List[str] = DTOField(..., description="Base token symbols", min_items=1)
    quote_symbols: List[str] = DTOField([], description="Quote token symbols."
                                        " If none provided, defaults to USD.")


@Model.describe(slug='band.price-by-symbol-bulk',
                version='1.0',
                display_name='Token Price    - from Oracle',
                description='Get token\'s price from Oracle',
                category='protocol',
                subcategory='band_protocol',
                tags=['price'],
                input=PriceSymbolsInput,
                output=Some[Price],
                errors=PRICE_DATA_ERROR_DESC)
class BandProtocolPriceBulk(Model):
    def run(self, input: PriceSymbolsInput):
        if self.context.network not in BAND_CONTRACTS:
            raise ModelDataError('Chain not supported')

        base_symbols = input.base_symbols
        quote_symbols = input.quote_symbols
        if len(quote_symbols) == 0:
            quote_symbols = ['USD'] * len(base_symbols)
        elif len(quote_symbols) != len(base_symbols):
            raise ModelDataError('No of base symbols should be equal to number of quote symbols.')

        contract = Contract(BAND_CONTRACTS[self.context.network])
        try:
            _ = contract.abi
        except (ModelDataError, ModelEngineError):
            contract = contract.set_abi(BAND_PROTOCOL_ABI, set_loaded=True)

        try:
            results = contract.functions.getReferenceDataBulk(
                base_symbols, quote_symbols).call()

            some: List[Price] = []
            for result in results:
                (rate, lastUpdatedBase, lastUpdatedQuote) = result
                some.append(Price(
                    price=rate/10**18,
                    src=f'{self.slug}|b:{lastUpdatedBase}|q:{lastUpdatedQuote}'))
            return Some(some=some)
        except Exception as err:
            raise ModelDataError('No possible feed/routing for one of the token pair') from err
