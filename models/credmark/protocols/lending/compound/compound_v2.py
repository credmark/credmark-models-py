import credmark.model
from credmark.model import ModelRunError

from credmark.types import (
    Address,
    Token,
    Contract,
)

from models.tmp_abi_lookup import (
    COMPOUND_ABI,
    ERC_20_ABI,
    ERC_20_TOKEN_CONTRACT_ABI,
    COMPOUND_CTOKEN_CONTRACT_ABI,
)

COMPOUND_ASSETS = {"REP": "0x1985365e9f78359a9B6AD760e32412f4a445E862",
                   "SAI": "0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359",
                   "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
                   "YFI": "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",
                   "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
                   "USDP": "0x8E870D67F660D95d5be530380D0eC0bd388289E1",
                   "SUSHI": "0x6B3595068778DD592e39A122f4f5a5cF09C90fE2",
                   "MKR": "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",
                   "BAT": "0x0D8775F648430679A709E98d2b0Cb6250d2887EF",
                   "ZRX": "0xE41d2489571d322189246DaFA5ebDe1F4699F498",
                   "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                   "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
                   "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
                   "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                   "TUSD": "0x0000000000085d4780B73119b644AE5ecd22b376",
                   "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                   "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                   "COMP": "0xc00e94Cb662C3520282E6f5717214004A7f26888"}


@credmark.model.describe(slug="compound.test",
                         version="1.0",
                         display_name="Compound Lending Pool Assets",
                         description="Compound assets for the main lending pool",
                         input=Token)
class CompoundGetAssets(credmark.model.Model):
    def try_or(self, func, default=None, expected_exc=(Exception,)):
        try:
            return func()
        except expected_exc:
            return default

    def run(self, input: Token) -> dict:
        # FIXME: remove abi
        input = Token(address=input.address, abi=ERC_20_ABI)

        if not input.address:
            raise ModelRunError(f'Input token is invalid, {input}')

        output = {}
        contract = Contract(
            # lending pool address for Compound
            address=Address("0x3FDA67f7583380E67ef93072294a7fAc882FD7E7").checksum,
            abi=COMPOUND_ABI
        )

        # converting the address to 'Address' type for safety
        comp_asset = contract.functions.markets(input.address.checksum).call()
        tokencontract = Contract(address=input.address.checksum, abi=ERC_20_TOKEN_CONTRACT_ABI)
        symbol = self.try_or(lambda: tokencontract.functions.symbol().call())
        decimals = tokencontract.functions.decimals().call()
        totalSupply = comp_asset[3]/pow(10, decimals)
        totalBorrows = comp_asset[6]/pow(10, decimals)
        output[symbol] = {'totalsupply': totalSupply, 'totalborrow': totalBorrows}

        return output


@credmark.model.describe(slug="compound-token-liability",
                         version="1.0",
                         display_name="Compound V2 token liability",
                         description="Compound V2 token liability at a given block number",
                         input=Token)
class CompoundV2GetTokenLiability(credmark.model.Model):
    def run(self, input: Token) -> dict:
        if not input.address:
            raise ModelRunError(f'Input token is invalid, {input}')

        output = {}
        tokenContract = Contract(
            address=input.address.checksum,
            abi=ERC_20_TOKEN_CONTRACT_ABI)

        symbol = tokenContract.functions.symbol().call()
        cTokenAddress = Address(COMPOUND_ASSETS[symbol]).checksum
        cTokenContract = Contract(
            address=cTokenAddress,
            abi=COMPOUND_CTOKEN_CONTRACT_ABI)

        totalLiquidity = cTokenContract.functions.totalSupply().call()
        totalBorrows = cTokenContract.functions.totalBorrows().call()
        decimals = cTokenContract.functions.decimals().call()
        totalLiquidity = float(totalLiquidity)/pow(10, decimals)
        totalBorrows = float(totalBorrows)/pow(10, decimals)

        output = {'result': {'token': symbol,
                             'totalLiquidity': totalLiquidity, 'totalBorrows': totalBorrows}}

        return output


@credmark.model.describe(slug="compound-token-asset",
                         version="1.0",
                         display_name="Compound V2 token liquidity",
                         description="Compound V2 token liquidity at a given block number",
                         input=Token)
class CompoundV2GetTokenAsset(credmark.model.Model):
    def run(self, input: Token) -> dict:
        if not input.address:
            raise ModelRunError(f'Input token is invalid, {input}')

        output = {}
        tokenContract = Contract(
            address=input.address.checksum,
            abi=ERC_20_TOKEN_CONTRACT_ABI)

        symbol = tokenContract.functions.symbol().call()
        cTokenAddress = Address(COMPOUND_ASSETS[symbol]).checksum
        cTokenContract = Contract(
            address=cTokenAddress,
            abi=COMPOUND_CTOKEN_CONTRACT_ABI)

        getCash = cTokenContract.functions.getCash().call()
        totalReserves = cTokenContract.functions.totalReserves().call()
        decimals = cTokenContract.functions.decimals().call()
        getCash = float(getCash)/pow(10, decimals)
        totalReserves = float(totalReserves)/pow(10, decimals)

        output = {'result': {'token': symbol, 'totalReserves': totalReserves, 'cash': getCash}}

        return output
