from typing import (
    List,
    Optional,
)

from credmark.cmf.model import Model

from credmark.cmf.model.errors import (
    ModelRunError,
    ModelDataError
)

from credmark.cmf.types import (
    Address,
    Contract,
    Token,
    Position,
    Portfolio,
)

from datetime import (
    date,
)

from credmark.cmf.types.series import BlockSeries

from credmark.dto import (
    DTO,
    EmptyInput,
    IterableListGenericDTO,
)

from credmark.dto import (
    DTO,
    DTOField,
    IterableListGenericDTO,
    PrivateAttr,
)

from typing import (
    Union,
    List,
)

from models.tmp_abi_lookup import (
    AAVE_V2_TOKEN_CONTRACT_ABI,
    ERC_20_TOKEN_CONTRACT_ABI,
)


class PriceList(IterableListGenericDTO[float]):
    prices: List[float] = DTOField(default=[], description='List of prices')
    token: Token
    src: Union[str, None] = DTOField(None, description='Source')
    _iterator: str = PrivateAttr('prices')

    class Config:
        schema_extra: dict = {
            'examples': [{'prices': [4.2, 2.3],
                          'token': {'address': '0x6B175474E89094C44Da98b954EedeAC495271d0F'}}]
        }

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


@Model.describe(slug="aave.overall-liabilities-portfolio",
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

        positions = []
        for asset in aave_assets:
            # self.logger.info(f'getting info for {asset=}')
            pos = self.context.run_model(slug='aave.token-liability',
                                         input=Token(address=asset),
                                         return_type=Position)
            positions.append(pos)

        return Portfolio(positions=positions)


@Model.describe(slug="aave.token-liability",
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
        # self.logger.info(f'info {getReservesData}, {getReservesData[7]}')

        aToken = Token(address=getReservesData[7])
        if aToken.total_supply is None:
            raise ModelDataError("total supply cannot be None")
        return Position(asset=aToken, amount=float(aToken.total_supply))


@Model.describe(slug="aave.lending-pool-assets",
                version="1.0",
                display_name="Aave V2 Lending Pool Assets",
                description="Aave V2 assets for the main lending pool",
                output=AaveDebtInfos)
class AaveV2GetAssets(Model):
    def run(self, input: EmptyInput) -> IterableListGenericDTO[AaveDebtInfo]:
        contract = Contract(
            # AAVE Lending Pool V2
            address=Address(AAVE_LENDING_POOL_V2).checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )

        aave_assets_address = contract.functions.getReservesList().call()

        aave_debts_infos = []
        for asset_address in aave_assets_address:
            info = self.context.run_model('aave.token-asset',
                                          input=Token(address=asset_address),
                                          return_type=AaveDebtInfo)
            aave_debts_infos.append(info)
        return AaveDebtInfos(aaveDebtInfos=aave_debts_infos)


@Model.describe(slug="aave.token-asset",
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
        if totalStableDebt is not None and totalVariableDebt is not None:
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
        else:
            raise ModelRunError(f'Unable to obtain {totalStableDebt=} and {totalVariableDebt=} '
                                f'for {aToken.address=}')


@Model.describe(slug="aave.token-asset-historical",
                version="1.0",
                display_name="Aave V2 token liquidity",
                description="Aave V2 token liquidity at a given block number",
                input=Token,
                output=BlockSeries[AaveDebtInfo])
class AaveV2GetTokenAssetHistorical(Model):
    def run(self, input: Token) -> BlockSeries:
        return self.context.historical.run_model_historical(
            'aave.token-asset',
            model_input=input,
            window='5 days',
            interval='1 day',
            model_return_type=AaveDebtInfo)



            
class HistoricalPriceInput(DTO):
    token: Token
    window: str  # e.g. '30 day'
    asOf: date


class DemoContractVaRInput(DTO):
    asOf: date
    window: str
    interval: int  # 1 or 2 or 10
    confidences: List[float]

class VaRHistoricalInput(IterableListGenericDTO[PriceList]):
    portfolio: Portfolio
    priceLists: List[PriceList]
    interval: int  # 1 or 2 or 10
    confidences: List[float]
    _iterator: str = PrivateAttr('priceLists')


@Model.describe(slug="aave.var",
                version="1.0",
                display_name="Aave V2 LCR",
                description="Aave V2 LCR",
                input=DemoContractVaRInput,
                output=dict)
class AaveV2GetVAR(Model):
    # def run(self, input: DemoContractVaRInput) -> dict:
    def run(self, input: DemoContractVaRInput) -> dict:
        
        contract = Contract(
            address=Address(AAVE_LENDING_POOL_V2).checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )

        aave_assets = contract.functions.getReservesList().call()

        positions = []
        for asset in aave_assets:
            reservesData = contract.functions.getReserveData(asset).call()
            stableDebtToken = Token(address=reservesData[8], abi=ERC_20_TOKEN_CONTRACT_ABI)
            try:
                symbol = stableDebtToken.symbol[10:]
                positions.append(Position(asset=Token(symbol=symbol), amount=100))
            except:
                symbol = None
            # print("Asset ", stableDebtToken, symbol)

        print("positions" , positions)
        portfolio = Portfolio(positions = positions)

        pls       = []
        pl_assets = set()

        for pos in portfolio:
            if pos.asset.address not in pl_assets:
                historical_price_input = HistoricalPriceInput(token  = pos.asset,
                                                              window = input.window,
                                                              asOf   = input.asOf)
                pl = self.context.run_model(slug        = 'finance.example-historical-price',
                                            input       = historical_price_input,
                                            return_type = PriceList)
                pls.append(pl)
                pl_assets.add(pos.asset.address)

        print("PLS", pls)

        var_input = VaRHistoricalInput(
            portfolio   = portfolio,
            priceLists  = pls,
            interval    = input.interval,
            confidences = input.confidences,
        )
        return self.context.run_model(slug='finance.var-engine-historical',
                                      input=var_input,
                                      return_type=dict)
