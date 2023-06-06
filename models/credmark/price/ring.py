# pylint: disable=line-too-long, pointless-string-statement


from credmark.cmf.model import Model
from credmark.cmf.types import Address, BlockNumberOutOfRangeError, Network, Some, Token
from web3.exceptions import BadFunctionCallOutput

from models.dtos.price import (
    AddressWithSerial,
    DexProtocol,
    DexProtocolInput,
    PrimaryTokenPairsInput,
    PrimaryTokenPairsOutput,
)

# credmark-dev run dex.ring0-tokens -b 17_100_000 -i '{"protocol": "uniswap-v3"}' -j

RING_MODEL_VERSION = '0.4'


@Model.describe(slug='dex.ring0-tokens',
                version=RING_MODEL_VERSION,
                display_name='DEX Tokens - Primary, or Ring0',
                description='Tokens to form primary trading pairs for new token issuance',
                category='protocol',
                subcategory='dex',
                tags=['uniswap-v2', 'uniswap-v3', 'sushiswap', 'pancakeswap-v2', 'pancakeswap-v3'],
                input=DexProtocolInput,
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
        Network.Mainnet: {
            **{protocol: (lambda: [Token('USDC'), Token('DAI'), Token('USDT')])
               for protocol in [DexProtocol.UniswapV2,
                                DexProtocol.UniswapV3,
                                DexProtocol.SushiSwap]},

            **{protocol: (lambda: [Token('USDC'), Token('USDT')])
               for protocol in [DexProtocol.PancakeSwapV2,
                                DexProtocol.PancakeSwapV3]},
        },
        Network.BSC: {
            # UITP/BOB on Uniswap V3 on BSC are not included because few connection to other tokens.
            **{protocol: (lambda: [Token('USDT'), Token('BUSD'), Token('USDC')])
               for protocol in [DexProtocol.UniswapV3,
                                DexProtocol.PancakeSwapV3,
                                DexProtocol.PancakeSwapV2]},
        },
        Network.Polygon: {
            # BOB is not part of ring1 due to limited connection to other tokens.
            # Moved Token('DAI') out to Ring1
            # Because we only support three tokens in Ring0 in order for triangulation for inter-ratios
            **{protocol: (lambda: [Token('USDC'), Token('USDT'), Token('miMATIC')])
               for protocol in [DexProtocol.UniswapV3]}
        }
    }

    def run(self, input: DexProtocolInput) -> Some[Address]:
        valid_tokens = []
        for t in self.RING0_TOKENS[self.context.network][input.protocol]():
            try:
                _ = (t.deployed_block_number is not None and
                     t.deployed_block_number >= self.context.block_number)
                valid_tokens.append(t.address)
            except (BadFunctionCallOutput, BlockNumberOutOfRangeError):
                pass
        return Some(some=valid_tokens)


# credmark-dev run dex.ring1-tokens -b 17_100_000 -i '{"protocol": "uniswap-v3"}' -j

@Model.describe(slug='dex.ring1-tokens',
                version=RING_MODEL_VERSION,
                display_name='DEX Tokens - Secondary, or Ring1',
                description='Tokens to form secondary trading pairs for new token issuance',
                category='protocol',
                subcategory='dex',
                tags=['uniswap-v2', 'uniswap-v3', 'sushiswap', 'pancakeswap-v2', 'pancakeswap-v3'],
                input=DexProtocolInput,
                output=Some[AddressWithSerial])
class DexSecondaryTokens(Model):
    RING1_TOKENS = {
        Network.Mainnet: {
            **{protocol: (lambda block_number:
                          [Token('WETH')] if block_number <= 17_385_780
                          else [Token('WETH'), Token('WBTC')])
               for protocol in [DexProtocol.UniswapV2,
                                DexProtocol.UniswapV3,
                                DexProtocol.SushiSwap]},

            **{protocol: (lambda _: [Token('WETH')])
               for protocol in [DexProtocol.PancakeSwapV2,
                                DexProtocol.PancakeSwapV3]},
        },
        Network.BSC: {
            **{protocol: (lambda _: [Token('WBNB'), Token('BTCB'), Token('ETH')])
               for protocol in [DexProtocol.UniswapV3,
                                DexProtocol.PancakeSwapV2,
                                DexProtocol.PancakeSwapV3]},
        },
        Network.Polygon: {
            **{protocol: (lambda _: [Token('WMATIC'), Token('WETH'), Token('WBTC'), Token('DAI')])
               for protocol in [DexProtocol.UniswapV3]}
        }
    }

    def run(self, input: DexProtocolInput) -> Some[AddressWithSerial]:
        valid_tokens = []
        serial_n = 0
        for t in self.RING1_TOKENS[self.context.network][input.protocol](self.context.block_number):
            try:
                _ = (t.deployed_block_number is not None and
                     t.deployed_block_number >= self.context.block_number)
                valid_tokens.append(AddressWithSerial(address=t.address, serial=serial_n))
                serial_n += 1
            except (BadFunctionCallOutput, BlockNumberOutOfRangeError):
                pass
        return Some(some=valid_tokens)

# credmark-dev run dex.primary-token-pairs -b 17_100_000 -i '{"addresses": ["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"],"protocol": "uniswap-v3"}' -j


@Model.describe(slug='dex.primary-token-pairs',
                version=RING_MODEL_VERSION,
                display_name='DEX pairs between tokens and primary tokens ',
                description='DEX candidate pairs (to be look up) between tokens and primary tokens (ring0/ring1)',
                category='protocol',
                subcategory='dex',
                tags=['uniswap-v2', 'uniswap-v3', 'sushiswap', 'pancakeswap-v2', 'pancakeswap-v3'],
                input=PrimaryTokenPairsInput,
                output=PrimaryTokenPairsOutput)
class PrimaryTokenPairs(Model):
    def run(self, input: PrimaryTokenPairsInput) -> PrimaryTokenPairsOutput:
        input_addresses = input.addresses
        ring0_tokens = self.context.run_model(
            'dex.ring0-tokens', DexProtocolInput(protocol=input.protocol),
            return_type=Some[Address], local=True).some
        primary_tokens_ring0 = ring0_tokens.copy()

        # _wbtc_address = Token('WBTC').address
        ring1_tokens_with_serial = (self.context.run_model(
            'dex.ring1-tokens', DexProtocolInput(protocol=input.protocol),
            return_type=Some[AddressWithSerial], local=True)
            .sorted(key=lambda t: t.serial))
        ring1_tokens = [t.address for t in ring1_tokens_with_serial]

        primary_tokens_ring1 = primary_tokens_ring0.copy()
        primary_tokens_ring1.extend(ring1_tokens)

        primary_tokens_ring1_step = {}
        for step in range(len(ring1_tokens)):
            primary_tokens_ring1_step[step] = primary_tokens_ring0.copy()
            primary_tokens_ring1_step[step].extend(ring1_tokens[:step])

        """
        TODO:
        # 1. In ring0 => all pair without self.
        # 2. In ring1+ => add tokens in ring0 and ring1 before
        # e.g. When ring1+ has [wbtc, wbtc2] => for wbtc, add weth; for wbtc2, add weth and wbtc2.
        # 3. _ => include all ring0 and ring1+
        """
        token_pairs: list[tuple[Address, Address]] = []

        for input_address in input_addresses:
            primary_tokens_in_use = primary_tokens_ring0
            if input_address not in ring0_tokens:
                if input_address not in ring1_tokens:
                    primary_tokens_in_use = primary_tokens_ring1
                else:
                    primary_tokens_in_use = primary_tokens_ring1_step[ring1_tokens.index(input_address)]

            for token_address in primary_tokens_in_use:
                if token_address == input_address:
                    continue
                if input_address.to_int() < token_address.to_int():
                    token_pairs.append((input_address, token_address))
                else:
                    token_pairs.append((token_address, input_address))

        return PrimaryTokenPairsOutput(pairs=token_pairs)
