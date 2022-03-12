import credmark.model
from credmark.types import Address, Contract, Token, BlockSeries
from models.tmp_abi_lookup import AAVE_V2_TOKEN_CONTRACT_ABI, ERC_20_TOKEN_CONTRACT_ABI


@credmark.model.describe(slug="aave-lending-pool-liabilities",
                         version="1.0",
                         display_name="Aave V2 Lending Pool liabilities",
                         description="Aave V2 liabilities for the main lending pool",
                         input=None)
class AaveV2GetLiability(credmark.model.Model):
    def run(self, input) -> dict:
        output = {}
        contract = self.context.web3.eth.contract(
            # lending pool address
            address=Address("0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9").checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )
        aave_assets = contract.functions.getReservesList().call()

        asset_output = {}
        for asset in aave_assets:

            res = self.context.run_model(
                'aave-token-liability', {"address": asset})

            token = res['result']['token']
            totalLiquidity = res['result']['totalLiquidity']

            asset_output[token] = totalLiquidity

        output = {'result': asset_output}
        return output


@credmark.model.describe(slug="aave-token-liability",
                         version="1.0",
                         display_name="Aave V2 token liability",
                         description="Aave V2 token liability at a given block number",
                         input=Contract)
class AaveV2GetTokenLiability(credmark.model.Model):
    output = {}

    def run(self, input: Contract) -> dict:
        contract = self.context.web3.eth.contract(
            # lending pool address
            address=Address("0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9").checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )

        getReservesData = contract.functions.getReserveData(input.address).call()

        aTokenContract = self.context.web3.eth.contract(
            address=getReservesData[7],
            abi=ERC_20_TOKEN_CONTRACT_ABI)
        totalLiquidity = aTokenContract.functions.totalSupply().call()
        decimals = aTokenContract.functions.decimals().call()
        totalLiquidity = float(totalLiquidity)/pow(10, decimals)

        symbol = str(aTokenContract.functions.symbol().call())[1:]

        output = {'result': {'token': symbol, 'totalLiquidity': totalLiquidity}}

        return output


@credmark.model.describe(slug="aave-lending-pool-assets",
                         version="1.0",
                         display_name="Aave V2 Lending Pool Assets",
                         description="Aave V2 assets for the main lending pool",
                         input=None)
class AaveV2GetAssets(credmark.model.Model):
    def run(self, input) -> dict:
        output = {}
        contract = self.context.web3.eth.contract(
            # lending pool address
            address=Address("0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9").checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )
        aave_assets = contract.functions.getReservesList().call()

        asset_output = {}
        for asset in aave_assets:

            getReservesData = contract.functions.getReserveData(asset).call()
            _atoken_asset = getReservesData[7]

            res = self.context.run_model(
                'aave-token-asset', input={"address": asset})

            token = res['result']['token']
            totalStableDebt = res['result']['totalStableDebt']
            totalVariableDebt = res['result']['totalVariableDebt']
            totalDebt = res['result']['totalDebt']

            asset_output[token] = {'totalStableDebt': totalStableDebt,
                                   'totalVariableDebt': totalVariableDebt, 'totalDebt': totalDebt}

        output = {'result': asset_output}
        return output


@credmark.model.describe(slug="aave-token-asset",
                         version="1.0",
                         display_name="Aave V2 token liquidity",
                         description="Aave V2 token liquidity at a given block number",
                         input=Token)
class AaveV2GetTokenAsset(credmark.model.Model):
    output = {}

    def run(self, input: Token) -> dict:

        contract = self.context.web3.eth.contract(
            # lending pool address
            address=Address("0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9").checksum,
            abi=AAVE_V2_TOKEN_CONTRACT_ABI
        )

        getReservesData = contract.functions.getReserveData(input.address).call()

        stableTokenContract = self.context.web3.eth.contract(
            address=getReservesData[8], abi=ERC_20_TOKEN_CONTRACT_ABI)
        totalStableDebt = stableTokenContract.functions.totalSupply().call()
        decimals = stableTokenContract.functions.decimals().call()
        totalStableDebt = float(totalStableDebt)/pow(10, decimals)

        variableTokenContract = self.context.web3.eth.contract(
            address=getReservesData[9], abi=ERC_20_TOKEN_CONTRACT_ABI)
        totalVariableDebt = variableTokenContract.functions.totalSupply().call()
        decimals = variableTokenContract.functions.decimals().call()
        totalVariableDebt = float(totalVariableDebt)/pow(10, decimals)

        totalDebt = totalStableDebt + totalVariableDebt

        symbol = str(stableTokenContract.functions.symbol().call())[10:]

        output = {'result': {'token': symbol, 'totalStableDebt': totalStableDebt,
                             'totalVariableDebt': totalVariableDebt, 'totalDebt': totalDebt}}

        return output


@credmark.model.describe(slug="aave-token-asset-historical",
                         version="1.0",
                         display_name="Aave V2 token liquidity",
                         description="Aave V2 token liquidity at a given block number",
                         input=Token,
                         output=BlockSeries)  # TODO add type
class AaveV2GetTokenAssetHistorical(credmark.model.Model):
    def run(self, input: Token) -> BlockSeries:
        return self.context.historical.run_model_historical(
            'aave-token-asset', model_input=input, window='5 days', interval='1 day')
