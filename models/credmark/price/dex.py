# pylint: disable=locally-disabled, unsupported-membership-test, pointless-string-statement
import sys
from abc import abstractmethod
from typing import List, Tuple

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (Address, Maybe, Network, Price, PriceWithQuote,
                                Some, Token)
from credmark.cmf.types.block_number import BlockNumberOutOfRangeError
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import EmptyInput
from models.dtos.price import (PRICE_DATA_ERROR_DESC, DexPoolAggregationInput,
                               DexPriceTokenInput, DexPriceTokensInput)
from models.dtos.pool import PoolPriceInfo
from web3.exceptions import BadFunctionCallOutput


@Model.describe(slug='dex.ring0-tokens',
                version='0.2',
                display_name='DEX Tokens - Primary, or Ring0',
                description='Tokens to form primary trading pairs for new token issuance',
                category='protocol',
                subcategory='dex',
                tags=['uniswap-v2', 'uniswap-v3', 'sushiswap'],
                output=Some[Address])
class DexPrimaryTokens(Model):
    """
    dex.ring0-tokens: ring0 tokens

    get_primary_token_tuples: a utility function to create token trading pairs
    - For ring0 tokens, with non-self ring0 tokens
    - For ring1 tokens (for now, weth), with each in rin0 tokens and ring1 tokens before it.
    - For rest, with ring0 and ring1 tokens
    """

    RING0_TOKENS = {
        Network.Mainnet: (lambda: [Token('USDC'), Token('DAI'), Token('USDT')])
    }

    def run(self, _) -> Some[Address]:
        valid_tokens = []
        for t in self.RING0_TOKENS[self.context.network]():
            try:
                _ = (t.deployed_block_number is not None and
                     t.deployed_block_number >= self.context.block_number)
                valid_tokens.append(t.address)
            except (BadFunctionCallOutput, BlockNumberOutOfRangeError):
                pass
        return Some(some=valid_tokens)


def get_primary_token_tuples(context, input_address: Address) -> List[Tuple[Address, Address]]:
    ring0_tokens = context.run_model('dex.ring0-tokens',
                                     input=EmptyInput(),
                                     return_type=Some[Address],
                                     local=True).some
    primary_tokens = ring0_tokens.copy()

    # WETH or native token's address
    weth_address = Token('WETH').address
    # _wbtc_address = Token('WBTC').address
    ring1_tokens = [weth_address]

    """
    TODO:
    # 1. In ring0 => all pair without self.
    # 2. In ring1+ => add tokens in ring0 and ring1 before
    # e.g. When ring1+ has [wbtc, wbtc2] => for wbtc, add weth; for wbtc2, add weth and wbtc2.
    # 3. _ => include all ring0 and ring1+
    """
    if input_address not in ring0_tokens:
        if input_address not in ring1_tokens:
            primary_tokens.extend(ring1_tokens)
        else:
            primary_tokens.extend(ring1_tokens[:ring1_tokens.index(input_address)])

    token_pairs = []

    for token_address in primary_tokens:
        if token_address == input_address:
            continue
        if input_address.to_int() < token_address.to_int():
            token_pairs.append((input_address.checksum, token_address.checksum))
            # TEST
            # token_pairs.append((Token(input_address).symbol, Token(token_address).symbol))
        else:
            token_pairs.append((token_address.checksum, input_address.checksum))
            # TEST
            # token_pairs.append((Token(token_address).symbol, Token(input_address).symbol))

    return token_pairs


@Model.describe(slug='price.pool-aggregator',
                version='1.10',
                display_name='Token Price from DEX pools, weighted by liquidity',
                description='Aggregate prices from pools weighted by liquidity',
                category='dex',
                subcategory='price',
                tags=['price'],
                input=DexPoolAggregationInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class PoolPriceAggregator(Model):
    def run(self, input: DexPoolAggregationInput) -> Price:
        all_pool_infos = input.some

        if len(all_pool_infos) == 0:
            raise ModelRunError(f'[{self.context.block_number}] No pool to aggregate for {input}')

        non_zero_pools = [
            ii.pool_address for ii in all_pool_infos
            if (ii.one_tick_liquidity0 > 1e-8 and ii.one_tick_liquidity1 > 1e-8)]

        zero_pools = [
            ii.pool_address for ii in all_pool_infos
            if (ii.one_tick_liquidity0 < 1e-8 or ii.one_tick_liquidity1 < 1e-8)]

        df = (Some(some=input.some)
              .to_dataframe()
              .assign(
            price_t=lambda x: x.price0.where(x.token0_address == input.address,
                                             x.price1) * x.ref_price,
            tick_liquidity_t=lambda x: x.one_tick_liquidity0.where(
                x.token0_address == input.address, x.one_tick_liquidity1))
              )

        price_src = (f'{",".join([x.split(".")[0] for x in df.src.unique()])}|'
                     f'Non-zero:{len(non_zero_pools)}|'
                     f'Zero:{len(zero_pools)}')

        if len(zero_pools) == len(all_pool_infos):
            # REPLACED with below
            # return Price(price=df.price_t.min(), src=price_src)
            raise ModelDataError(f'There is no liquidity in {len(zero_pools)} pools '
                                 f'for {input.address}.')

        if len(input.some) == 1:
            return Price(price=df.price_t[0], src=price_src)

        if input.debug:
            print(df, file=sys.stderr)

        product_of_price_liquidity = (df.price_t * df.tick_liquidity_t ** input.weight_power).sum()
        sum_of_liquidity = (df.tick_liquidity_t ** input.weight_power).sum()
        price = product_of_price_liquidity / sum_of_liquidity
        return Price(price=price, src=f'{price_src}|{input.weight_power}')


class DexWeightedPrice(Model):
    @abstractmethod
    def run(self, input):
        ...

    def aggregate_pool(self, model_slug, input: DexPriceTokenInput):
        pool_price_infos = self.context.run_model(model_slug,
                                                  input=input)

        pool_aggregator_input = DexPoolAggregationInput(**input.dict(),
                                                        **pool_price_infos)

        return PoolPriceAggregator(self.context).run(pool_aggregator_input)


@Model.describe(slug='uniswap-v3.get-weighted-price-maybe',
                version='1.8',
                display_name='Uniswap v3 - get price weighted by liquidity',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                tags=['price'],
                input=DexPriceTokenInput,
                output=Maybe[Price],
                errors=PRICE_DATA_ERROR_DESC)
class UniswapV3WeightedPriceMaybe(DexWeightedPrice):
    def run(self, input: DexPriceTokenInput) -> Maybe[Price]:
        try:
            price = self.context.run_model('uniswap-v3.get-weighted-price',
                                           input=input,
                                           return_type=Price)
            return Maybe(just=price)
        except ModelRunError as err:
            if 'No pool to aggregate' in err.data.message:
                return Maybe.none()
            raise


@Model.describe(slug='uniswap-v3.get-weighted-price',
                version='1.8',
                display_name='Uniswap v3 - get price weighted by liquidity',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                tags=['price'],
                input=DexPriceTokenInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class UniswapV3WeightedPrice(DexWeightedPrice):
    def run(self, input: DexPriceTokenInput) -> Price:
        return self.aggregate_pool('uniswap-v3.get-pool-info-token-price', input)


@Model.describe(slug='uniswap-v2.get-weighted-price',
                version='1.8',
                display_name='Uniswap v2 - get price weighted by liquidity',
                description='The Uniswap v2 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v2',
                tags=['price'],
                input=DexPriceTokenInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class UniswapV2WeightedPrice(DexWeightedPrice):
    def run(self, input: DexPriceTokenInput) -> Price:
        return self.aggregate_pool('uniswap-v2.get-pool-info-token-price', input)


@Model.describe(slug='sushiswap.get-weighted-price',
                version='1.8',
                display_name='Sushi v2 (Uniswap V2) - get price weighted by liquidity',
                description='The Sushi v2 pools that support a token contract',
                category='protocol',
                subcategory='sushi-v2',
                tags=['price'],
                input=DexPriceTokenInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class SushiV2GetAveragePrice(DexWeightedPrice):
    def run(self, input: DexPriceTokenInput) -> Price:
        return self.aggregate_pool('sushiswap.get-pool-info-token-price', input)


@Model.describe(slug='price.dex-pool',
                version='0.4',
                display_name='',
                description='The Current Credmark Supported Price Algorithms',
                developer='Credmark',
                category='price',
                subcategory='dex',
                tags=['dex', 'price'],
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class PriceInfoFromDex(Model):
    DEX_POOL_PRICE_INFO_MODELS: List[str] = ['uniswap-v2.get-pool-info-token-price',
                                             'sushiswap.get-pool-info-token-price',
                                             'uniswap-v3.get-pool-info-token-price']

    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        # For testing with other power, set this = default power for the token here
        # if input.address == '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': # WETH
        #    input.weight_power = 4.0
        # if input.address == '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9':  # AAVE
        #    input.weight_power = 4.0

        model_inputs = [{"modelSlug": slug, "modelInputs": [input]}
                        for slug in self.DEX_POOL_PRICE_INFO_MODELS]

        def _use_compose():
            all_pool_infos_results = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': 'compose.map-inputs',
                       'modelInputs': model_inputs},
                return_type=MapInputsOutput[dict, MapInputsOutput[dict, Some[PoolPriceInfo]]])

            all_pool_infos = []
            for dex_n, dex_result in enumerate(all_pool_infos_results):
                if dex_result.output is not None:
                    for pool_result in dex_result.output:
                        if pool_result.output is not None:
                            all_pool_infos.extend(pool_result.output)
                        elif pool_result.error is not None:
                            self.logger.error(pool_result.error)
                            raise ModelRunError(
                                (f'Error with models({self.context.block_number}).' +
                                 f'{model_inputs[dex_n]["modelSlug"].replace("-","_")}' +
                                 f'({pool_result.input}). ' +
                                 pool_result.error.message))
                elif dex_result.error is not None:
                    self.logger.error(dex_result.error)
                    raise ModelRunError(
                        (f'Error with models({self.context.block_number}).' +
                         f'{model_inputs[dex_n]}. ' +
                         dex_result.error.message))
                else:
                    raise ModelRunError('compose.map-inputs: output/error cannot be both None')
            return all_pool_infos

        def _use_for(local):
            all_pool_infos = []
            for m_input in model_inputs:
                infos = self.context.run_model(m_input['modelSlug'],
                                               m_input['modelInputs'][0],
                                               Some[PoolPriceInfo],
                                               local=local)
                all_pool_infos.extend(infos.some)
            return all_pool_infos

        return Some[PoolPriceInfo](some=_use_for(local=False))


@Model.describe(slug='price.dex-blended',
                version='1.17',
                display_name='Credmark Token Price from Dex',
                description='The Current Credmark Supported Price Algorithms',
                developer='Credmark',
                category='price',
                subcategory='dex',
                tags=['dex', 'price'],
                input=DexPriceTokenInput,
                output=PriceWithQuote,
                errors=PRICE_DATA_ERROR_DESC)
class PriceFromDexModel(Model):
    """
    Return token's price
    """

    def run(self, input: DexPriceTokenInput) -> PriceWithQuote:
        addr_maybe = self.context.run_model('token.underlying-maybe',
                                            input=input,
                                            return_type=Maybe[Address],
                                            local=True)
        if addr_maybe.just is not None:
            input.address = addr_maybe.just

        all_pool_infos = self.context.run_model('price.dex-pool',
                                                input=input,
                                                return_type=Some[PoolPriceInfo],
                                                local=True).some

        pool_aggregator_input = DexPoolAggregationInput(
            **input.dict(),
            some=all_pool_infos)

        price = PoolPriceAggregator(self.context).run(pool_aggregator_input)

        # Above code replaces code below as a saving to a model call
        # price = self.context.run_model('price.pool-aggregator',
        #                              input=pool_aggregator_input,
        #                              return_type=Price,
        #                              local=True)

        return PriceWithQuote.usd(**price.dict())


@Model.describe(slug='price.dex-db-prefer',
                version='0.4',
                display_name='Credmark Token Price from Dex (Prefer to use DB)',
                description='Retrieve price from DB or call model',
                developer='Credmark',
                category='price',
                subcategory='dex',
                tags=['dex', 'price'],
                input=Token,
                output=PriceWithQuote,
                errors=PRICE_DATA_ERROR_DESC)
class PriceFromDexPreferModel(Model):
    """
    Return token's price from Dex with Chainlink as fallback

    **`price.quote`** calls `chainlink`, `curve` then `price.dex-db-prefer`

    **`price.cex`** calls `chainlink` only.
    **'price.dex'** calls `price.dex-db-prefer` then calls `curve`
        - `price.dex-db-prefer` calls `price.dex-db`, then `price.dex-blended` (uniswap v2 / v3 and sushiswap)

    """

    def run(self, input: DexPriceTokenInput) -> PriceWithQuote:
        try:
            price_dex = self.context.run_model('price.dex-db', input=input, local=True)
            if price_dex['liquidity'] > 1e-08:
                return PriceWithQuote.usd(price=price_dex['price'], src=price_dex['protocol'])
            raise ModelDataError(f'There is no liquidity for {input.address}.')
        except (ModelDataError, ModelRunError) as err:
            if "No price for" in err.data.message or "No pool to aggregate for" in err.data.message:
                return self.context.run_model(
                    'price.dex-blended',
                    input={'address': input.address},
                    return_type=PriceWithQuote)
            raise


@Model.describe(slug='price.dex-blended-maybe',
                version='0.4',
                display_name='Token price - Credmark',
                description='The Current Credmark Supported Price Algorithms',
                developer='Credmark',
                category='price',
                subcategory='dex',
                tags=['dex', 'price'],
                input=DexPriceTokenInput,
                output=Maybe[PriceWithQuote])
class PriceFromDexModelMaybe(Model):
    """
    Return token's price
    """

    def run(self, input: Token) -> Maybe[PriceWithQuote]:
        try:
            price = self.context.run_model('price.dex-blended',
                                           input=input,
                                           return_type=PriceWithQuote)
            return Maybe(just=price)
        except ModelRunError as err:
            if 'No pool to aggregate' in err.data.message:
                return Maybe.none()
            raise


@Model.describe(slug='price.dex-blended-tokens',
                version='0.2',
                display_name='Token price - Credmark',
                description='The Current Credmark Supported Price Algorithms',
                developer='Credmark',
                category='price',
                subcategory='dex',
                tags=['dex', 'price'],
                input=DexPriceTokensInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class PriceFromDexModelTokens(Model):
    """
    Return token's price
    """

    def run(self, input: DexPriceTokensInput) -> Price:
        token_input = None
        all_pool_infos = []
        for token in input:
            token_input = DexPriceTokenInput(**token.dict(), **input.dict())

            pool_infos = self.context.run_model('price.dex-pool',
                                                input=token_input,
                                                return_type=Some[PoolPriceInfo],
                                                local=True).some

            for x in pool_infos:
                if x.token0_address == token.address:
                    x.token0_address = input.tokens[-1].address
                    x.token0_symbol = input.tokens[-1].symbol

                if x.token1_address == token.address:
                    x.token1_address = input.tokens[-1].address
                    x.token1_symbol = input.tokens[-1].symbol

            all_pool_infos += pool_infos

        # (Some(some=all_pool_infos).to_dataframe()
        # [['token0_address', 'token1_address', 'token0_symbol', 'token1_symbol']])

        if token_input is not None:
            pool_aggregator_input = DexPoolAggregationInput(
                **token_input.dict(),
                some=all_pool_infos)

            return PoolPriceAggregator(self.context).run(pool_aggregator_input)

        raise ModelRunError(f'No Token has been specified {input}')
