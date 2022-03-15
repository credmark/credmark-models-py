from typing import List
import credmark.model
from credmark.types import Address, Contract, Token, BlockSeries, Position, Portfolio
from credmark.types.dto import DTO, IterableListGenericDTO
from models.tmp_abi_lookup import AAVE_V2_TOKEN_CONTRACT_ABI, ERC_20_TOKEN_CONTRACT_ABI


class AaveDebtInfo(DTO):
    token: Token
    totalStableDebt: int
    totalVariableDebt: int
    totalDebt: int


class AaveDebtInfos(IterableListGenericDTO[AaveDebtInfo]):
    aaveDebtInfos: List[AaveDebtInfo]
    _iterator: str = 'aaveDebtInfos'


AAVE_LENDING_POOL_V2 = '0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9'


@credmark.model.describe(slug="aave.overall-liabilities-portfolio",
                         version="1.0",
                         display_name="Aave V2 Lending Pool overall liabilities",
                         description="Aave V2 liabilities for the main lending pool",
                         input=None,
                         output=Portfolio)
class AaveV2GetLiability(credmark.model.Model):

    def run(self, input) -> Portfolio:
        contract = Contract(
            address=Address(AAVE_LENDING_POOL_V2).checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )

        aave_assets = contract.functions.getReservesList().call()

        return Portfolio(positions=[self.context.run_model(
            slug='aave.token-liability',
            input=Token(address=asset),
            return_type=Position) for asset in aave_assets])


@credmark.model.describe(slug="aave.token-liability",
                         version="1.0",
                         display_name="Aave V2 token liability",
                         description="Aave V2 token liability at a given block number",
                         input=Token,
                         output=Position)
class AaveV2GetTokenLiability(credmark.model.Model):

    def run(self, input: Contract) -> Position:
        contract = Contract(
            address=Address(AAVE_LENDING_POOL_V2).checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )

        getReservesData = contract.functions.getReserveData(input.address).call()

        aToken = Token(
            address=getReservesData[7],
            abi=ERC_20_TOKEN_CONTRACT_ABI)

        return Position(token=aToken, amount=aToken.total_supply())


@credmark.model.describe(slug="aave.lending-pool-assets",
                         version="1.0",
                         display_name="Aave V2 Lending Pool Assets",
                         description="Aave V2 assets for the main lending pool",
                         input=None,
                         output=AaveDebtInfos)
class AaveV2GetAssets(credmark.model.Model):
    def run(self, input) -> IterableListGenericDTO[AaveDebtInfo]:
        contract = Contract(
            # AAVE Lending Pool V2
            address=Address(AAVE_LENDING_POOL_V2).checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )
        aave_assets = contract.functions.getReservesList().call()

        return AaveDebtInfos(aaveDebtInfos=[self.context.run_model(
            'aave.token-asset',
            input=Token(address=asset),
            return_type=AaveDebtInfo) for asset in aave_assets])


@credmark.model.describe(slug="aave.token-asset",
                         version="1.0",
                         display_name="Aave V2 token liquidity",
                         description="Aave V2 token liquidity at a given block number",
                         input=Token,
                         output=AaveDebtInfo)
class AaveV2GetTokenAsset(credmark.model.Model):

    def run(self, input: Token) -> AaveDebtInfo:

        contract = Contract(
            # AAVE Lending Pool V2
            address=Address(AAVE_LENDING_POOL_V2).checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )

        getReservesData = contract.functions.getReserveData(input.address).call()
        stableToken = Token(
            address=getReservesData[8], abi=ERC_20_TOKEN_CONTRACT_ABI)
        totalStableDebt = stableToken.total_supply()

        totalVariableDebt = Token(
            address=getReservesData[9], abi=ERC_20_TOKEN_CONTRACT_ABI).total_supply()

        totalDebt = totalStableDebt + totalVariableDebt

        return AaveDebtInfo(
            token=Token(symbol=stableToken.symbol, decimals=stableToken.decimals),
            totalStableDebt=totalStableDebt,
            totalVariableDebt=totalVariableDebt,
            totalDebt=totalDebt)


@credmark.model.describe(slug="aave.token-asset-historical",
                         version="1.0",
                         display_name="Aave V2 token liquidity",
                         description="Aave V2 token liquidity at a given block number",
                         input=Token,
                         output=BlockSeries)
class AaveV2GetTokenAssetHistorical(credmark.model.Model):
    def run(self, input: Token) -> BlockSeries:
        return self.context.historical.run_model_historical(
            'aave.token-asset', model_input=input, window='5 days', interval='1 day', model_version='1.0')
