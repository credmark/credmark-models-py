# pylint: disable=line-too-long, pointless-string-statement, too-many-arguments

from abc import abstractmethod
from typing import Optional

from credmark.cmf.model import Model
from credmark.cmf.types import Address, Price, Some

from models.dtos.price import (
    AddressWithSerial,
    DexPriceTokenInput,
    DexProtocolInput,
)


class UniswapRefPriceMeta(Model):
    @abstractmethod
    def run(self, input):
        ...

    def get_ref_price(self,
                      model_input,
                      token0_addr: Address, token1_addr: Address,
                      token0_symbol: str, token1_symbol: str,
                      ratio_price0: float, ratio_price1: float,
                      fee: Optional[float]):
        """
        1. If ring0-ring0: use ref_price_slug to get ref_price
        2. If ring0/ring1-ring1: use ring0 and some ring1 (prior to that) to get the price
        2. If ring0/ring1-X: use all ring0/ring1 to price

        For a setup of ring0(USDC/USDT/DAI) and ring1 (WETH/WBTC) and ring2 (AAVE)
        - USDC's reference tokens are ring0 tokens
        - WETH's reference tokens are ring0 tokens
        - WBTC's reference tokens are ring0 + WETH tokens
        - AAVE's reference tokens are ring0 + WETH + WBTC tokens

        - For USDC-DAI pool, it's ring0 pool, use model_input.ref_price_slug
        - For WETH-USDC pool, WETH (token0) is not in USDC's reference tokens while
                              USDC (token1) is in WETH's reference tokens.
                              USDC (token1) is the reference token.
        - For AAVE-WETH pool, AAVE (token0) is not in WETH's reference tokens while
                              WETH (token1) is in AAVE's reference tokens.
                              WETH (token1) is the reference token.
        """

        fee_str = fee if fee is not None else ''

        ref_price = 1.0

        # pylint:disable=locally-disabled, too-many-locals, too-many-statements
        ring0_tokens = self.context.run_model(
            'dex.ring0-tokens', DexProtocolInput(protocol=model_input.protocol),
            return_type=Some[Address]).some

        ring1_tokens_with_serial = (self.context.run_model(
            'dex.ring1-tokens', DexProtocolInput(protocol=model_input.protocol),
            return_type=Some[AddressWithSerial])
            .sorted(key=lambda t: t.serial))
        ring1_tokens = [t.address for t in ring1_tokens_with_serial]

        if token0_addr in ring0_tokens:
            token0_ref_tokens = [x for x in ring0_tokens if x != token0_addr]
        elif token0_addr in ring1_tokens:
            token0_ref_tokens = ring0_tokens + ring1_tokens[:ring1_tokens.index(token0_addr)]
        else:
            token0_ref_tokens = ring0_tokens + ring1_tokens

        if token1_addr in ring0_tokens:
            token1_ref_tokens = [x for x in ring0_tokens if x != token1_addr]
        elif token1_addr in ring1_tokens:
            token1_ref_tokens = ring0_tokens + ring1_tokens[:ring1_tokens.index(token1_addr)]
        else:
            token1_ref_tokens = ring0_tokens + ring1_tokens

        is_ring0_pool = token0_addr in ring0_tokens and token1_addr in ring0_tokens

        if is_ring0_pool:
            # aka: token0_addr in token1_ref_tokens and token1_addr in token0_ref_tokens
            if model_input.ref_price_slug is not None:
                self.logger.info(f'Pool: {token0_symbol}/{token1_symbol}/{fee_str} use {model_input.ref_price_slug}')
                ref_price_ring0 = self.context.run_model(
                    model_input.ref_price_slug, {}, return_type=dict)
                # Use the reference price to scale the tick price. Note the cross-reference is used here.
                # token0 = tick_price0 * token1 = tick_price0 * ref_price of token1
                ratio_price0 *= ref_price_ring0[token1_addr]
                ratio_price1 *= ref_price_ring0[token0_addr]
            else:
                self.logger.info(f'Pool: {token0_symbol}/{token1_symbol}/{fee_str} use default ref_price=1')
        elif token0_addr in token1_ref_tokens and token1_addr not in token0_ref_tokens:
            self.logger.info(f'Pool: {token0_symbol}/{token1_symbol}/{fee_str}, ref_token: {token0_symbol}')
            ref_price = self.context.run_model(
                slug=model_input.price_slug,
                input=DexPriceTokenInput(
                    address=token0_addr,
                    weight_power=model_input.weight_power),
                return_type=Price).price
        elif token0_addr not in token1_ref_tokens and token1_addr in token0_ref_tokens:
            self.logger.info(f'Pool: {token0_symbol}/{token1_symbol}/{fee_str}, ref_token: {token1_symbol}')
            ref_price = self.context.run_model(
                slug=model_input.price_slug,
                input=DexPriceTokenInput(
                    address=token1_addr,
                    weight_power=model_input.weight_power),
                return_type=Price).price
        else:
            # aka: token0_addr not in token1_ref_tokens and token1_addr not in token0_ref_tokens:
            ref_price = 0
            msg = ('There is no primary token in this pool: '
                   f'{token0_addr}/{token0_symbol} and {token1_addr}/{token1_symbol} with fee={fee_str}'
                   f' in {token0_ref_tokens=} and {token1_ref_tokens=}')
            self.logger.warning(msg)
            # We allow pool info to be calculated for non-pricing pools.
            # raise ModelRunError(msg)

        return ref_price, ratio_price0, ratio_price1
