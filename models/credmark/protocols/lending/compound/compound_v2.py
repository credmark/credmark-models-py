from typing import List
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError, ModelDataError

from credmark.cmf.types import (
    Address,
    Token,
    Contract,
)

from credmark.dto import (
    DTO,
    EmptyInput,
    IterableListGenericDTO,
)


from models.tmp_abi_lookup import (
    COMPOUND_ABI,
    ERC_20_TOKEN_CONTRACT_ABI,
    COMPOUND_CTOKEN_CONTRACT_ABI,
)

COMPOUND_ASSETS = {
    "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
    "BAT": "0x0D8775F648430679A709E98d2b0Cb6250d2887EF",
    "COMP": "0xc00e94Cb662C3520282E6f5717214004A7f26888",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "FEI": '0x956F47F50A910163D8BF957Cf5846D573E7f87CA',
    "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    "MKR": "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",
    "REP": "0x1985365e9f78359a9B6AD760e32412f4a445E862",
    "SAI": "0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359",
    "SUSHI": "0x6B3595068778DD592e39A122f4f5a5cF09C90fE2",
    "TUSD": "0x0000000000085d4780B73119b644AE5ecd22b376",
    "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDP": "0x8E870D67F660D95d5be530380D0eC0bd388289E1",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "WBTC2": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # same as WBTC
    "YFI": "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",
    "ZRX": "0xE41d2489571d322189246DaFA5ebDe1F4699F498",

}

COMPOUND_CTOKEN = {
    'cAAVE': '0xe65cdb6479bac1e22340e4e755fae7e509ecd06c',
    'cBAT': '0x6c8c6b02e7b2be14d4fa6022dfd6d75921d90e4e',
    'cCOMP': '0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4',
    'cDAI': '0x5d3a536e4d6dbd6114cc1ead35777bab948e3643',
    'cETH': '0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5',
    'cFEI': '0x7713dd9ca933848f6819f38b8352d9a15ea73f67',
    'cLINK': '0xface851a4921ce59e912d19329929ce6da6eb0c7',
    'cMKR': '0x95b4ef2869ebd94beb4eee400a99824bf5dc325b',
    'cREP': '0x158079ee67fce2f58472a96584a73c7ab9ac95c1',
    'cSAI': '0xf5dce57282a584d2746faf1593d3121fcac444dc',
    'cSUSHI': '0x4b0181102a0112a2ef11abee5563bb4a3176c9d7',
    'cTUSD': '0x12392f67bdf24fae0af363c24ac620a2f67dad86',
    'cUNI': '0x35a18000230da775cac24873d00ff85bccded550',
    'cUSDC':  '0x39aa39c021dfbae8fac545936693ac917d5e7563',
    'cUSDP': '0x041171993284df560249b57358f931d9eb7b925d',
    'cUSDT': '0xf650c3d88d12db855b8bf7d11be6c55a4e07dcc9',
    'cWBTC': '0xc11b1268c1a384e55c48c2391d8d480264a3a7f4',
    'cWBTC2': '0xccf4429db6322d5c611ee964527d42e5d685dd6a',
    'cYFI': '0x80a2ae356fc9ef4305676f7a3e2ed04e12c33946',
    'cZRX': '0xb3319f5d18bc0d84dd1b4825dcde5d5f7266d407'
}

assert sorted(COMPOUND_ASSETS.keys()) == sorted(
    ['WETH' if t == 'cETH' else t[1:] for t, _ in COMPOUND_CTOKEN.items()])

COMPOUND_COMP = '0xc00e94cb662c3520282e6f5717214004a7f26888'

COMPOUND_COMPTROLLER = '0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b'
COMPOUND_GOVERNANCE = '0xc0da02939e1441f497fd74f78ce7decb17b66529'
COMPOUND_TIMELOCK = '0x6d903f6003cca6255d85cca4d3b5e5146dc33925'

# Pool(Contract)
# LendingPool(Pool)
# CompoundLendingPool(LendingPool)


@ Model.describe(slug="compound.test",
                 version="1.0",
                 display_name="Compound Lending Pool Assets",
                 description="Compound assets for the main lending pool",
                 input=Token)
class CompoundGetAssets(Model):
    def run(self, input: Token) -> dict:
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
        token = Token(address=input.address.checksum)
        symbol = token.symbol
        decimals = token.decimals
        totalSupply = comp_asset[3]/pow(10, decimals)
        totalBorrows = comp_asset[6]/pow(10, decimals)
        output[symbol] = {'totalsupply': totalSupply, 'totalborrow': totalBorrows}

        return output


class CompoundDebtInfo(DTO):
    inputSymbol: str
    tokenName: str
    cTokenName: str
    token: Token
    cToken: Token
    totalLiquidity: float
    totalBorrows: float
    totalReserves: float


class CompoundDebtInfos(IterableListGenericDTO[CompoundDebtInfo]):
    compoundDebtInfos: List[CompoundDebtInfo]
    _iterator: str = 'CompoundDebtInfos'


@Model.describe(slug="compound.all-liability",
                version="1.0",
                display_name="Compound V2 token liability",
                description="Compound V2 token liability at a given block number",
                input=EmptyInput,
                output=CompoundDebtInfos)
class CompoundV2TotalLiability(Model):

    def run(self, input: EmptyInput) -> CompoundDebtInfos:

        debts = []

        for _, tokenAddress in COMPOUND_CTOKEN.items():
            debt = self.context.run_model(slug='compound.token-liability',
                                          input=Token(address=tokenAddress))
            debts.append(debt)

        return CompoundDebtInfos(compoundDebtInfos=debts)


@Model.describe(slug="compound.token-liability",
                version="1.0",
                display_name="Compound V2 token liability",
                description="Compound V2 token liability at a given block number",
                input=Token,
                output=CompoundDebtInfo)
class CompoundV2GetTokenLiability(Model):
    def run(self, input: Token) -> CompoundDebtInfo:
        cToken = Token(address=input.address,
                       abi=COMPOUND_CTOKEN_CONTRACT_ABI)

        if input.symbol == 'cETH':
            token = Token(address=COMPOUND_ASSETS['WETH'])
        elif (input.address == '0xf5dce57282a584d2746faf1593d3121fcac444dc' and
              input.symbol == 'cDAI'):
            # When input = cSAI, it has been renamed to cDAI in the contract.
            # We will still call up SAI
            token = Token(address=COMPOUND_ASSETS['SAI'])
        else:
            if input.symbol is None:
                raise ModelDataError("Symbol cannot be none")
            token = Token(address=COMPOUND_ASSETS[input.symbol[1:]])

        self.logger.info(f'{cToken.address, cToken.symbol}')

        assert cToken.functions.isCToken().call()
        # ( assert cToken.proxy_for is not None and
        #   cToken.functions.implementation().call() == cToken.proxy_for.address )
        assert cToken.functions.admin().call() == Address(COMPOUND_TIMELOCK)
        assert cToken.functions.comptroller().call() == Address(COMPOUND_COMPTROLLER)
        assert cToken.functions.symbol().call()
        if cToken.name != 'Compound Ether':
            assert cToken.functions.underlying().call() == token.address

        totalLiquidity = cToken.functions.totalSupply().call()
        totalBorrows = cToken.functions.totalBorrows().call()
        totalReserves = cToken.functions.totalReserves().call()
        decimals = cToken.functions.decimals().call()

        totalLiquidity = float(totalLiquidity)/pow(10, decimals)
        totalBorrows = float(totalBorrows)/pow(10, decimals)
        totalReserves = float(totalReserves)/pow(10, decimals)
        if input.symbol is None:
            raise ModelDataError("symbol cannot be None")
        
        if token.name is None:
            raise ModelDataError("Token name cannot be None")

        if cToken.name is None:
            raise ModelDataError("cToken name cannot be None")
            
        debt = CompoundDebtInfo(inputSymbol=input.symbol,
                                tokenName=token.name,
                                cTokenName=cToken.name,
                                token=token,
                                cToken=cToken,
                                totalLiquidity=totalLiquidity,
                                totalBorrows=totalBorrows,
                                totalReserves=totalReserves)

        return debt


@Model.describe(slug="compound.token-asset",
                version="1.0",
                display_name="Compound V2 token liquidity",
                description="Compound V2 token liquidity at a given block number",
                input=Token)
class CompoundV2GetTokenAsset(Model):
    def run(self, input: Token) -> dict:
        if not input.address:
            raise ModelRunError(f'Input token is invalid, {input}')

        output = {}
        tokenContract = Contract(
            address=input.address.checksum,
            abi=ERC_20_TOKEN_CONTRACT_ABI)

        symbol = tokenContract.functions.symbol().call()
        cTokenAddress = Address(COMPOUND_CTOKEN[symbol]).checksum
        cToken = Token(address=cTokenAddress,
                       abi=COMPOUND_CTOKEN_CONTRACT_ABI)

        getCash = cToken.functions.getCash().call()
        totalReserves = cToken.functions.totalReserves().call()
        decimals = cToken.functions.decimals().call()
        getCash = float(getCash)/pow(10, decimals)
        totalReserves = float(totalReserves)/pow(10, decimals)

        output = {'result': {'token': symbol, 'totalReserves': totalReserves, 'cash': getCash}}

        return output
