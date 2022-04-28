from typing import List, Optional
from credmark.cmf.model import Model
from credmark.cmf.types import (
    Address,
    Contract,
    Token,
    Position,
    Portfolio,
)
from credmark.cmf.types.series import BlockSeries
from credmark.dto import DTO, IterableListGenericDTO

from models.tmp_abi_lookup import (
    AAVE_V2_TOKEN_CONTRACT_ABI,
    ERC_20_TOKEN_CONTRACT_ABI,
)


class AaveDebtInfo(DTO):
    token: Token
    aToken: Token
    stableDebtToken: Token
    variableDebtToken: Token
    interestRateStrategyContract: Optional[Contract]
    totalStableDebt: int
    totalVariableDebt: int
    totalDebt: int


class AaveDebtInfos(IterableListGenericDTO[AaveDebtInfo]):
    aaveDebtInfos: List[AaveDebtInfo]
    _iterator: str = 'aaveDebtInfos'


AAVE_LENDING_POOL_V2 = '0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9'


@Model.describe(slug="contrib.aave-overall-liabilities-portfolio",
                version="1.0",
                display_name="Aave V2 Lending Pool overall liabilities",
                description="Aave V2 liabilities for the main lending pool",
                output=Portfolio)
class AaveV2GetLiability(Model):

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


@Model.describe(slug="contrib.aave-token-liability",
                version="1.0",
                display_name="Aave V2 token liability",
                description="Aave V2 token liability at a given block number",
                input=Token,
                output=Position)
class AaveV2GetTokenLiability(Model):

    def run(self, input: Contract) -> Position:
        contract = Contract(
            address=Address(AAVE_LENDING_POOL_V2).checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )

        getReservesData = contract.functions.getReserveData(input.address).call()

        aToken = Token(
            address=getReservesData[7],
            abi=ERC_20_TOKEN_CONTRACT_ABI)

        return Position(asset=aToken, amount=aToken.total_supply)


@Model.describe(slug="contrib.aave-lending-pool-assets",
                version="1.0",
                display_name="Aave V2 Lending Pool Assets",
                description="Aave V2 assets for the main lending pool",
                output=AaveDebtInfos)
class AaveV2GetAssets(Model):
    def run(self, input) -> IterableListGenericDTO[AaveDebtInfo]:
        contract = Contract(
            # AAVE Lending Pool V2
            address=Address(AAVE_LENDING_POOL_V2).checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )

        aave_assets_address = contract.functions.getReservesList().call()

        aave_debts = AaveDebtInfos(aaveDebtInfos=[self.context.run_model(
            'aave.token-asset',
            input=Token(address=asset_address),
            return_type=AaveDebtInfo) for asset_address in aave_assets_address])

        return aave_debts


@Model.describe(slug="contrib.aave-token-asset",
                version="1.0",
                display_name="Aave V2 token liquidity",
                description="Aave V2 token liquidity at a given block number",
                input=Token,
                output=AaveDebtInfo)
class AaveV2GetTokenAsset(Model):

    def run(self, input: Token) -> AaveDebtInfo:

        contract = Contract(
            # AAVE Lending Pool V2
            address=Address(AAVE_LENDING_POOL_V2).checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )

        reservesData = contract.functions.getReserveData(input.address).call()

        aToken = Token(address=reservesData[7], abi=ERC_20_TOKEN_CONTRACT_ABI)
        stableDebtToken = Token(address=reservesData[8], abi=ERC_20_TOKEN_CONTRACT_ABI)
        variableDebtToken = Token(address=reservesData[9], abi=ERC_20_TOKEN_CONTRACT_ABI)
        interestRateStrategyContract = Contract(address=reservesData[10])

        totalStableDebt = stableDebtToken.total_supply
        totalVariableDebt = variableDebtToken.total_supply
        totalDebt = totalStableDebt + totalVariableDebt

        return AaveDebtInfo(
            token=input,
            aToken=aToken,
            stableDebtToken=stableDebtToken,
            variableDebtToken=variableDebtToken,
            interestRateStrategyContract=interestRateStrategyContract,
            totalStableDebt=totalStableDebt,
            totalVariableDebt=totalVariableDebt,
            totalDebt=totalDebt)


@Model.describe(slug="contrib.aave-token-asset-historical",
                 version="1.0",
                 display_name="Aave V2 token liquidity",
                 description="Aave V2 token liquidity at a given block number",
                 input=Token,
                 output=BlockSeries[AaveDebtInfo])
class AaveV2GetTokenAssetHistorical(Model):
    def run(self, input: Token) -> BlockSeries[AaveDebtInfo]:
        return self.context.historical.run_model_historical(
            'aave.token-asset',
            model_input=input,
            window='5 days',
            interval='1 day',
            model_version='1.0')



@Model.describe(slug="contrib.aave-LCR",
                          version="1.0",
                          display_name="Aave V2 LCR",
                          description="Current LCR value for Aave V2",
                          input=None,
                          output=None)
class AaveV2GetLCR(Model):
    def run(self, input) -> IterableListGenericDTO[AaveDebtInfo]:
        contract = Contract(
            # lending pool address
            address=Address("0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9").checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )
        aave_assets = contract.functions.getReservesList().call()

        TotalAssets = 0
        TotalLiabilities = 0
        MARKET_CAP = 0
        for asset in aave_assets:
            getReservesData = contract.functions.getReserveData(asset).call()
            MARKET_CAP += getReservesData[4] / pow(10,18)
            stableToken = Token(
                address=getReservesData[8], abi=ERC_20_TOKEN_CONTRACT_ABI)
            totalStableDebt = stableToken.total_supply()

            totalVariableDebt = Token(
                address=getReservesData[9], abi=ERC_20_TOKEN_CONTRACT_ABI).total_supply()

            totalDebt    = totalStableDebt + totalVariableDebt
            # print("Assets : ", totalDebt , stableToken.decimals ,totalDebt / pow(10, stableToken.decimals ), stableToken.symbol )
            TotalAssets += totalDebt / pow(10, stableToken.decimals )

            aToken = Token( 
                address=getReservesData[7],
                abi=ERC_20_TOKEN_CONTRACT_ABI)

            # print("Supply ", aToken.total_supply(),  aToken.decimals , aToken.total_supply() / pow(10, aToken.decimals ), aToken.symbol  )    
            TotalLiabilities += aToken.total_supply() / pow(10, aToken.decimals )


        print("TotalAssets ", TotalAssets)
        print("TotalLiabilities ", TotalLiabilities)
        print("MARKET_CAP : ", MARKET_CAP)


        LCR = (MARKET_CAP * 0.7 ) / ( TotalLiabilities* 0.2 + TotalAssets* 0.1 )

        print("LCR : ", LCR)



@Model.describe(slug="contrib.aave-VAR",
                version="1.0",
                display_name="Aave V2 VAR",
                description="Current LCR value for Aave V2",
                input=None,
                output=None)
class AaveV2GetVAR(Model):
    
    def run(self, input) -> IterableListGenericDTO[AaveDebtInfo]:
        contract = Contract(
            # AAVE Lending Pool V2
            address=Address(AAVE_LENDING_POOL_V2).checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )

        aave_assets_address = contract.functions.getReservesList().call()
        print(aave_assets_address)

        for asset in aave_assets:
            getReservesData = contract.functions.getReserveData(asset).call()
            MARKET_CAP += getReservesData[4] / pow(10,18)
            stableToken = Token(
                address=getReservesData[8], abi=ERC_20_TOKEN_CONTRACT_ABI)

            historical_price = self.context.historical.run_model_historical(
                    'token.price', window='1 year', interval='1 day',
                    model_version='1.0', model_input=stableToken.symbol)

            print(historical_price)




