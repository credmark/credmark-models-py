import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelInputError
from credmark.cmf.types import Address, Contract, Contracts, Network, Records, Some, Token, Tokens
from credmark.dto import DTO, DTOField, EmptyInputSkipTest, IterableListGenericDTO, PrivateAttr

from models.credmark.protocols.dexes.uniswap.constant import V3_POOL_FEES
from models.credmark.protocols.dexes.uniswap.uniswap_v3_meta import UniswapV3PoolMeta
from models.dtos.pool import DexPoolInput, PoolPriceInfo
from models.dtos.price import DexPoolPriceInput, DexPriceTokenInput, DexProtocol, PriceWeight
from models.tmp_abi_lookup import UNISWAP_V3_FACTORY_ABI, UNISWAP_V3_POOL_ABI

V3_FACTORY_ADDRESS = {
    k: Address("0xe3fc2cB6E8c2671816D15B556B47375Afb2C29bD")
    for k in [
        Network.Oasys,
    ]
}


class TealswapV3FactoryMeta:
    FACTORY_ADDRESS = V3_FACTORY_ADDRESS
    PROTOCOL = DexProtocol.TealswapV3
    POOL_FEES = V3_POOL_FEES
    FACTORY_ABI = UNISWAP_V3_FACTORY_ABI


class TealswapV3Pool(Contract):
    class Config:
        schema_extra = {
            # CRV / WETH
            "examples": [
                {
                    "address": "0xFC99D1c02D27DE07DfE0dCd878CDe86ee59c5f6B",
                    "_test_multi": {"chain_id": 137},
                }
            ],
            "test_multi": True,
        }


class TealswapV3DexPoolPriceInput(TealswapV3Pool, DexPoolPriceInput):
    class Config:
        schema_extra = {
            "examples": [
                {
                    "address": "0xFC99D1c02D27DE07DfE0dCd878CDe86ee59c5f6B",  # USDC / WETH
                    "price_slug": "tealswap-v3.get-weighted-price",
                    "ref_price_slug": "tealswap-v3.get-ring0-ref-price",
                    "weight_power": 4.0,
                    "protocol": "tealswap-v3",
                    "_test_multi": {"chain_id": 137},
                }
            ],
            "test_multi": True,
        }


TEALSWAPV3_VERSION = "0.1"


@Model.describe(
    slug="tealswap-v3.get-factory",
    version=TEALSWAPV3_VERSION,
    display_name="Tealswap V3 - get factory",
    description="Returns the address of Tealswap V3 factory contract",
    category="protocol",
    subcategory="tealswap-v3",
    output=Contract,
)
class TealswapV3GetFactory(UniswapV3PoolMeta, TealswapV3FactoryMeta):
    def run(self, _) -> Contract:
        return self.get_factory(self.FACTORY_ADDRESS[self.context.network], self.FACTORY_ABI)


@Model.describe(
    slug="tealswap-v3.get-pools-by-pair",
    version=TEALSWAPV3_VERSION,
    display_name="Tealswap V3 get pool for a pair of tokens",
    description=("Returns the addresses of the pool of input tokens"),
    category="protocol",
    subcategory="tealswap-v3",
    input=DexPoolInput,
    output=Contracts,
)
class TealswapV3GetPool(UniswapV3PoolMeta, TealswapV3FactoryMeta):
    def run(self, input: DexPoolInput) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_by_pair(
            factory_addr,
            self.FACTORY_ABI,
            [(input.token0.address, input.token1.address)],
            self.POOL_FEES,
        )
        return Contracts.from_addresses(pools)


@Model.describe(
    slug="tealswap-v3.all-pools-events",
    version=TEALSWAPV3_VERSION,
    display_name="Tealswap v3 all pairs",
    description="Returns the addresses of all pairs on Tealswap V3 protocol",
    category="protocol",
    subcategory="tealswap-v3",
    input=EmptyInputSkipTest,
    output=Records,
)
class TealswapV3AllPoolsEvents(UniswapV3PoolMeta, TealswapV3FactoryMeta):
    def run(self, _) -> Records:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_all_pairs_events(
            factory_addr, self.FACTORY_ABI, _from_block=0, _to_block=self.context.block_number
        )


@Model.describe(
    slug="tealswap-v3.all-pools-ledger",
    version=TEALSWAPV3_VERSION,
    display_name="Tealswap v3 Token Pools - from ledger",
    description="The Tealswap v3 pools that support a token contract",
    category="protocol",
    subcategory="tealswap-v3",
    input=EmptyInputSkipTest,
    output=Records,
)
class TealswapV3AllPoolsLedger(UniswapV3PoolMeta, TealswapV3FactoryMeta):
    def run(self, _) -> Records:
        return self.get_all_pools_ledger(
            self.FACTORY_ADDRESS[self.context.network], self.FACTORY_ABI
        )


class Pool(DTO):
    block_number: int
    log_index: int
    transaction_hash: str
    pool_address: Address
    token0: Address
    token1: Address
    fee: int
    tickSpacing: int


class Pools(IterableListGenericDTO[Pool]):
    """
    Iterable list of Pool instances.
    """

    pools: list[Pool] = DTOField(default=[], description="An iterable list of Pool Objects")
    _iterator: str = PrivateAttr("pools")


@Model.describe(
    slug="tealswap-v3.get-pools-by-token",
    version=TEALSWAPV3_VERSION,
    display_name="Tealswap v3 Token Pools",
    description="The Tealswap v3 pools that support a token contract",
    category="protocol",
    subcategory="tealswap-v3",
    input=Token,
    output=Pools,
)
class TealswapV3GetPoolsByToken(Model):
    def run(self, input: Token) -> Pools:
        df = self.context.run_model(
            "tealswap-v3.all-pools-events", EmptyInputSkipTest(), return_type=Records
        ).to_dataframe()

        token_pools = [
            Pool(
                block_number=row["block_number"],
                log_index=row["log_index"],
                transaction_hash=row["transaction_hash"],
                pool_address=row["pool_address"],
                token0=Address(row["token0"]),
                token1=Address(row["token1"]),
                fee=row["fee"],
                tickSpacing=row["tickSpacing"],
            )
            for _, row in df.iterrows()
            if (Address(row["token0"]) == input.address)
            or (Address(row["token1"]) == input.address)
        ]

        return Pools(pools=token_pools)


class LiquidityProvider(DTO):
    class Block(DTO):
        block_number: int
        timestamp: str

    address: Address = DTOField(description="Address of holder")
    liquidity: int = DTOField(description="Liquidity provided by account")
    liquidity_scaled: float = DTOField(description="Liquidity scaled to token decimals for account")
    first_transfer_block: Block
    last_transfer_block: Block


class LiquidityProvidersOutput(IterableListGenericDTO[LiquidityProvider]):
    providers: list[LiquidityProvider] = DTOField(
        default=[], description="List of liquidity prviders"
    )
    total_providers: int = DTOField(description="Total number of liquidity providers")

    _iterator: str = PrivateAttr("holders")


class GetLiquidityProvidersInput(Token):
    pool: Contract | None = DTOField(
        None,
        description="Filter for this pool only. If not provided, get for all pools of the token.",
    )
    limit: int = DTOField(100, gt=0, description="Limit the number of holders that are returned")
    offset: int = DTOField(
        0, ge=0, description="Omit a specified number of holders from beginning of result set"
    )
    min_amount: int = DTOField(
        -1,
        description="Minimum liquidity for a provider to be included. Default is -1, a minimum \
            balance greater than 0",
    )
    max_amount: int = DTOField(
        -1, description="Maximum liquidity for a provider to be included. Default is -1, no maximum"
    )


@Model.describe(
    slug="tealswap-v3.get-liquidity-providers",
    version=TEALSWAPV3_VERSION,
    display_name="Tealswap v3 Token Pools",
    description="The Tealswap v3 pools that support a token contract",
    category="protocol",
    subcategory="tealswap-v3",
    input=GetLiquidityProvidersInput,
    output=LiquidityProvidersOutput,
)
class TealswapV3GetLiquidityProviders(Model):
    def run(self, input: GetLiquidityProvidersInput) -> LiquidityProvidersOutput:
        with self.context.ledger.TokenBalance as q:
            order_by = q.field("liquidity").dquote().desc()
            having = (
                q.RAW_AMOUNT.as_numeric().sum_().gt(0)
                if input.min_amount == -1
                else q.RAW_AMOUNT.as_numeric().sum_().ge(input.unscaled(input.min_amount))
            )

            if input.max_amount != -1:
                having = having.and_(
                    q.RAW_AMOUNT.as_numeric().sum_().le(input.unscaled(input.max_amount))
                )

            if input.pool is not None:
                input.pool.set_abi(UNISWAP_V3_POOL_ABI, set_loaded=True)
                token0 = Address(input.pool.functions.token0().call())
                token1 = Address(input.pool.functions.token1().call())
                if input.address not in (token0, token1):
                    raise ModelInputError(
                        "Input token does not match token0 or token1 of the provided pool"
                    )
                counterparty_cond = q.COUNTERPARTY_ADDRESS.eq(input.pool.address)
            else:
                pools = self.context.run_model(
                    "tealswap-v3.get-pools-by-token", input=input, return_type=Pools
                )

                counterparty_cond = q.COUNTERPARTY_ADDRESS.in_(
                    [pool.pool_address for pool in pools]
                )

            df = q.select(
                aggregates=[
                    (q.RAW_AMOUNT.as_numeric().sum_(), "liquidity"),
                    (q.BLOCK_NUMBER.min_(), "first_block_number"),
                    (q.BLOCK_TIMESTAMP.min_(), "first_block_timestamp"),
                    (q.BLOCK_NUMBER.max_(), "last_block_number"),
                    (q.BLOCK_TIMESTAMP.max_(), "last_block_timestamp"),
                    ("COUNT(*) OVER()", "total_providers"),
                ],
                where=q.TOKEN_ADDRESS.eq(input.address).and_(counterparty_cond),
                group_by=[q.ADDRESS],
                having=having,
                order_by=order_by.comma_(q.ADDRESS),
                limit=input.limit,
                offset=input.offset,
                bigint_cols=["liquidity"],
                analytics_mode=True,
            ).to_dataframe()

            if df.empty:
                total_providers = 0
            else:
                total_providers = df["total_providers"].values[0]
                if total_providers is None:
                    total_providers = 0

            return LiquidityProvidersOutput(
                providers=[
                    LiquidityProvider(
                        address=Address(row["address"]),
                        liquidity=row["liquidity"],
                        liquidity_scaled=input.scaled(row["liquidity"]),
                        first_transfer_block=LiquidityProvider.Block(
                            block_number=row["first_block_number"],
                            timestamp=row["first_block_timestamp"],
                        ),
                        last_transfer_block=LiquidityProvider.Block(
                            block_number=row["last_block_number"],
                            timestamp=row["last_block_timestamp"],
                        ),
                    )
                    for _, row in df.iterrows()
                ],
                total_providers=total_providers,
            )


class GetSwapsByPoolInput(Contract):
    from_block: int


@Model.describe(
    slug="tealswap-v3.get-swaps-by-pool",
    version=TEALSWAPV3_VERSION,
    display_name="Tealswap v3 Token Pools",
    description="The Tealswap v3 pools that support a token contract",
    category="protocol",
    subcategory="tealswap-v3",
    input=GetSwapsByPoolInput,
    output=Records,
)
class TealswapV3GetSwapsByPool(Model):
    def run(self, input: GetSwapsByPoolInput) -> Records:
        input.set_abi(UNISWAP_V3_POOL_ABI, set_loaded=True)
        df = pd.DataFrame(
            input.fetch_events(input.events.Swap, by_range=100_000, from_block=input.from_block)
        )

        df = df[
            [
                "logIndex",
                "transactionIndex",
                "transactionHash",
                "blockNumber",
                "sender",
                "recipient",
                "amount0",
                "amount1",
                "sqrtPriceX96",
                "liquidity",
                "tick",
            ]
        ]
        df["transactionHash"] = df["transactionHash"].apply(lambda x: x.hex())

        df.rename(
            columns={
                "blockNumber": "block_number",
                "logIndex": "log_index",
                "transactionIndex": "transaction_index",
                "transactionHash": "transaction_hash",
            },
            inplace=True,
        )

        return Records.from_dataframe(df)


@Model.describe(
    slug="tealswap-v3.get-pools",
    version=TEALSWAPV3_VERSION,
    display_name="Tealswap v3 Token Pools",
    description="The Tealswap v3 pools that support a token contract",
    category="protocol",
    subcategory="tealswap-v3",
    input=Token,
    output=Contracts,
)
class TealswapV3GetPoolsForToken(UniswapV3PoolMeta, TealswapV3FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(
            factory_addr, self.FACTORY_ABI, self.PROTOCOL, [input.address], self.POOL_FEES
        )
        return Contracts.from_addresses(pools)


@Model.describe(
    slug="tealswap-v3.get-pools-ledger",
    version=TEALSWAPV3_VERSION,
    display_name="Tealswap v3 Token Pools",
    description="The Tealswap v3 pools that support a token contract - use ledger",
    category="protocol",
    subcategory="tealswap-v3",
    input=Token,
    output=Contracts,
)
class TealswapV3GetPoolsForTokenLedger(UniswapV3PoolMeta, TealswapV3FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_pools_for_tokens_ledger(
            factory_addr, self.FACTORY_ABI, self.PROTOCOL, input.address, self.POOL_FEES
        )


@Model.describe(
    slug="tealswap-v3.get-pools-tokens",
    version=TEALSWAPV3_VERSION,
    display_name="Tealswap v3 Token Pools",
    description="The Tealswap v3 pools that support a token contract",
    category="protocol",
    subcategory="tealswap-v3",
    input=Tokens,
    output=Contracts,
)
class TealswapV3GetPoolsForTokens(UniswapV3PoolMeta, TealswapV3FactoryMeta):
    def run(self, input: Tokens) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(
            factory_addr,
            self.FACTORY_ABI,
            self.PROTOCOL,
            [tok.address for tok in input.tokens],
            self.POOL_FEES,
        )
        return Contracts.from_addresses(list(set(pools)))


@Model.describe(
    slug="tealswap-v3.get-ring0-ref-price",
    version=TEALSWAPV3_VERSION,
    display_name="Tealswap v3 Ring0 Reference Price",
    description="The Tealswap v3 pools that support the ring0 tokens",
    category="protocol",
    subcategory="tealswap-v3",
    input=PriceWeight,
    output=dict,
)
class TealswapV3GetRing0RefPrice(UniswapV3PoolMeta, TealswapV3FactoryMeta):
    def run(self, input: PriceWeight) -> dict:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_ref_price(
            factory_addr, self.FACTORY_ABI, self.PROTOCOL, input.weight_power, self.POOL_FEES
        )


@Model.describe(
    slug="tealswap-v3.get-pool-info-token-price",
    version=TEALSWAPV3_VERSION,
    display_name="Tealswap v3 Token Pools Price ",
    description="Gather price and liquidity information from pools",
    category="protocol",
    subcategory="tealswap-v3",
    input=DexPriceTokenInput,
    output=Some[PoolPriceInfo],
)
class TealswapV3GetTokenPoolInfo(UniswapV3PoolMeta, TealswapV3FactoryMeta):
    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model("tealswap-v3.get-pools", input, return_type=Contracts)
        return self.get_pools_info(
            input,
            pools,
            model_slug="tealswap-v3.get-pool-price-info",
            price_slug="tealswap-v3.get-weighted-price",
            ref_price_slug="tealswap-v3.get-ring0-ref-price",
            _protocol=self.PROTOCOL,
        )
