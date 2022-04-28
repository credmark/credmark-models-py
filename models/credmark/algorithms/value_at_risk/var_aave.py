from datetime import datetime, timezone

from credmark.cmf.model import Model
from credmark.dto import EmptyInput

from credmark.cmf.types import (
    Position,
    Portfolio,
    BlockNumber,
    PriceList,
)

from models.credmark.algorithms.value_at_risk.dto import (
    HistoricalPriceInput,
    VaRHistoricalInput,
    ContractVaRInput,
)


from models.credmark.protocols.lending.aave.aave_v2 import (
    AaveDebtInfos,
)


@Model.describe(slug="finance.var-aave",
                version="1.0",
                display_name="Aave V2 LCR",
                description="Aave V2 LCR",
                input=ContractVaRInput,
                output=dict)
class AaveV2GetVAR(Model):
    def run(self, input: ContractVaRInput) -> dict:
        """
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

        1. Checkout the aave-v2.lending-pool-assets model
        2. Get the portfolio on the input.asOf date.
        """

        asof_dt = datetime.combine(input.asOf, datetime.max.time(), tzinfo=timezone.utc)
        asof_block_number = BlockNumber.from_timestamp(asof_dt)

        debts = self.context.run_model('aave-v2.lending-pool-assets',
                                       input=EmptyInput(),
                                       return_type=AaveDebtInfos,
                                       block_number=asof_block_number)

        n_debts = len(debts.aaveDebtInfos)

        positions = []
        self.logger.info('Aave net asset = Asset - liability')
        for n_dbt, dbt in enumerate(debts):
            self.logger.debug(f'{n_dbt+1}/{n_debts} '
                              f'Token info: {dbt.token.symbol=} {dbt.token.address=} '
                              f'{dbt.token.name=} {dbt.token.total_supply=} '
                              f'{dbt.token.decimals=}')
            self.logger.debug(f'{dbt.aToken.address=} {dbt.totalLiquidity_qty=} '
                              f'from {dbt.totalSupply_qty=}-{dbt.totalDebt_qty=}')
            positions.append(Position(amount=dbt.totalLiquidity_qty, asset=dbt.token))
        portfolio = Portfolio(positions=positions)

        pls = []
        pl_assets = set()

        for pos in portfolio:
            if pos.asset.address not in pl_assets:
                historical_price_input = HistoricalPriceInput(token=pos.asset,
                                                              window=input.window,
                                                              asOf=input.asOf)
                pl = self.context.run_model(slug='finance.example-historical-price',
                                            input=historical_price_input,
                                            return_type=PriceList)
                pls.append(pl)
                pl_assets.add(pos.asset.address)

        print("PLS", pls)

        var_input = VaRHistoricalInput(
            portfolio=portfolio,
            priceLists=pls,
            interval=input.interval,
            confidences=input.confidences,
        )
        return self.context.run_model(slug='finance.var-engine-historical',
                                      input=var_input,
                                      return_type=dict)
