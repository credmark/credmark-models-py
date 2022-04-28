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

        print("positions", positions)
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
