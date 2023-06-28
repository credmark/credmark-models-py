from typing import List
from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError, ModelEngineError
from credmark.cmf.types import Contract, NetworkDict, Network, PriceWithQuote, Some

from models.dtos.price import PriceInput
from models.tmp_abi_lookup import BAND_PROTOCOL_ABI

PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='No possible feed/routing for token pair')

contracts = NetworkDict(str, {
    Network.Avalanche: '0x75B01902D9297fD381bcF3B155a8cEAC78F5A35E',
    Network.BSC: '0xDA7a001b254CD22e46d3eAB04d937489c93174C3',
    Network.Mainnet: '0xDA7a001b254CD22e46d3eAB04d937489c93174C3',
    Network.Fantom: '0xDA7a001b254CD22e46d3eAB04d937489c93174C3',
    Network.Optimism: '0xDA7a001b254CD22e46d3eAB04d937489c93174C3',
})


@Model.describe(slug='price.oracle-band-protocol',
                version='1.0',
                display_name='Token Price - from Oracle',
                description='Get token\'s price from Oracle',
                category='protocol',
                subcategory='band_protocol',
                tags=['price'],
                input=PriceInput,
                output=PriceWithQuote,
                errors=PRICE_DATA_ERROR_DESC)
class PriceOracleBandProtocol(Model):
    def run(self, input: PriceInput):
        if self.context.network not in contracts:
            raise ModelDataError('Chain not supported')

        contract = Contract(contracts[self.context.network])
        try:
            _ = contract.abi
        except (ModelDataError, ModelEngineError):
            contract = contract.set_abi(BAND_PROTOCOL_ABI, set_loaded=True)

        try:
            (rate, lastUpdatedBase, lastUpdatedQuote) = contract.functions.getReferenceData(
                input.base.symbol, input.quote.symbol).call()
            return PriceWithQuote(price=rate/10**18,
                                  src=f'{self.slug}|b:{lastUpdatedBase}|q:{lastUpdatedQuote}',
                                  quoteAddress=input.quote.address)
        except:
            raise ModelDataError('No possible feed/routing for token pair')


@Model.describe(slug='price.oracle-band-protocol-multiple',
                version='1.0',
                display_name='Token Price - from Oracle',
                description='Get token\'s price from Oracle',
                category='protocol',
                subcategory='band_protocol',
                tags=['price'],
                input=Some[PriceInput],
                output=Some[PriceWithQuote],
                errors=PRICE_DATA_ERROR_DESC)
class PriceOracleBandProtocolMultiple(Model):
    def run(self, input: Some[PriceInput]) -> Some[PriceWithQuote]:
        if self.context.network not in contracts:
            raise ModelDataError('Chain not supported')

        contract = Contract(contracts[self.context.network])
        try:
            _ = contract.abi
        except (ModelDataError, ModelEngineError):
            contract = contract.set_abi(BAND_PROTOCOL_ABI, set_loaded=True)

        bases = [price_input.base.symbol for price_input in input]
        quotes = [price_input.quote.symbol for price_input in input]
        try:
            results = contract.functions.getReferenceDataBulk(
                bases, quotes).call()

            some: List[PriceWithQuote] = []
            for _input, result in zip(input.some, results):
                (rate, lastUpdatedBase, lastUpdatedQuote) = result
                some.append(PriceWithQuote(
                    price=rate/10**18,
                    src=f'{self.slug}|b:{lastUpdatedBase}|q:{lastUpdatedQuote}',
                    quoteAddress=_input.quote.address))
            return Some(some=some)
        except:
            raise ModelDataError('No possible feed/routing for token pair')
