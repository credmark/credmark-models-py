import credmark.model
from credmark.types import Address, AddressDTO
from credmark.types.dto import DTO, DTOField
from credmark.types import Position
from ....tmp_abi_lookup import ERC_20_TOKEN_CONTRACT_ABI, COMPOUND_CTOKEN_CONTRACT_ABI

COMPOUND_ASSETS = {'REP': '0x158079ee67fce2f58472a96584a73c7ab9ac95c1',
                   'SAI': '0xf5dce57282a584d2746faf1593d3121fcac444dc',
                   'TUSD': '0x12392f67bdf24fae0af363c24ac620a2f67dad86',
                   'FEI': '0x7713dd9ca933848f6819f38b8352d9a15ea73f67',
                   'BAT': '0x6c8c6b02e7b2be14d4fa6022dfd6d75921d90e4e',
                   'AAVE': '0xe65cdb6479bac1e22340e4e755fae7e509ecd06c',
                   'WBTC': '0xccf4429db6322d5c611ee964527d42e5d685dd6a',
                   'USDP': '0x041171993284df560249b57358f931d9eb7b925d',
                   'COMP': '0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4',
                   'SUSHI': '0x4b0181102a0112a2ef11abee5563bb4a3176c9d7',
                   'MKR': '0x95b4ef2869ebd94beb4eee400a99824bf5dc325b',
                   'ZRX': '0xb3319f5d18bc0d84dd1b4825dcde5d5f7266d407',
                   'YFI': '0x80a2ae356fc9ef4305676f7a3e2ed04e12c33946',
                   'LINK': '0xface851a4921ce59e912d19329929ce6da6eb0c7',
                   'DAI': '0x5d3a536e4d6dbd6114cc1ead35777bab948e3643',
                   'UNI': '0x35a18000230da775cac24873d00ff85bccded550',
                   'USDT': '0xf650c3d88d12db855b8bf7d11be6c55a4e07dcc9',
                   'WETH': '0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5',
                   'USDC': '0x39aa39c021dfbae8fac545936693ac917d5e7563'}


@credmark.model.describe(slug="compound-token-liability",
                         version="1.0",
                         display_name="Compound V2 token liability",
                         description="Compound V2 token liability at a given block number",
                         input=AddressDTO)
class CompoundV2GetTokenLiability(credmark.model.Model):
    def run(self, input: AddressDTO) -> dict:
        output = {}
        tokenContract = self.context.web3.eth.contract(
            address=input.address,
            abi=ERC_20_TOKEN_CONTRACT_ABI)

        symbol = tokenContract.functions.symbol().call()
        cTokenAddress = self.context.web3.toChecksumAddress(COMPOUND_ASSETS[symbol])
        cTokenContract = self.context.web3.eth.contract(
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
                         input=AddressDTO)
class CompoundV2GetTokenAsset(credmark.model.Model):
    def run(self, input: AddressDTO) -> dict:
        output = {}
        tokenContract = self.context.web3.eth.contract(
            address=input.address,
            abi=ERC_20_TOKEN_CONTRACT_ABI)

        symbol = tokenContract.functions.symbol().call()
        cTokenAddress = self.context.web3.toChecksumAddress(COMPOUND_ASSETS[symbol])
        cTokenContract = self.context.web3.eth.contract(
            address=cTokenAddress,
            abi=COMPOUND_CTOKEN_CONTRACT_ABI)

        getCash = cTokenContract.functions.getCash().call()
        totalReserves = cTokenContract.functions.totalReserves().call()
        decimals = cTokenContract.functions.decimals().call()
        getCash = float(getCash)/pow(10, decimals)
        totalReserves = float(totalReserves)/pow(10, decimals)

        output = {'result': {'token': symbol, 'totalReserves': totalReserves, 'cash': getCash}}

        return output
