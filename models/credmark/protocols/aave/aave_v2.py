import credmark.model
from credmark.types import Address, AddressDTO
from credmark.types.dto import DTO, DTOField
from ....tmp_abi_lookup import AAVE_V2_TOKEN_CONTRACT_ABI, ERC_20_TOKEN_CONTRACT_ABI
@credmark.model.describe(slug="aave-lending-pool-assets",
                         version="1.0",
                         display_name="Aave V2 Lending Pool Assets",
                         description="Aave V2 assets for the main lending pool",
                         input=None)
class AaveV2GetAssets(credmark.model.Model):
    def run(self, input:AddressDTO) -> dict:
        output = {}
        contract = self.context.web3.eth.contract(
                                address="0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9", # lending pool address
                                abi = AAVE_V2_TOKEN_CONTRACT_ABI
                                )
        aave_assets = contract.functions.getReservesList().call()
        totalSupply = 0
        for asset in aave_assets:
            asset_output   = []
            getReservesData = contract.functions.getReserveData(asset).call()
            atoken_asset = getReservesData[7]
            print("Asset : ", asset, atoken_asset)
            symbol , totalSupply = self.context.run_model('aave-token-asset',{"address": atoken_asset})
            output[symbol] = totalSupply
        print(output)
    def try_or(self, func, default=None, expected_exc=(Exception,)):
        try:
            return func()
        except expected_exc:
            return default
@credmark.model.describe(slug="aave-token-asset",
                         version="1.0",
                         display_name="Aave V2 token liquidity",
                         description="Aave V2 token liquidity at a given block number",
                         input=AddressDTO)
class AaveV2GetTokenAsset(credmark.model.Model):
    output = {}
    def run(self, input:AddressDTO) -> dict:
        contract = self.context.web3.eth.contract(
                    address="0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9", # lending pool address
                    abi = AAVE_V2_TOKEN_CONTRACT_ABI
                    )

        getReservesData = contract.functions.getReserveData(input.address).call()

        tokenContract = self.context.web3.eth.contract(address=getReservesData[7], abi= ERC_20_TOKEN_CONTRACT_ABI)
        totalSupply   = tokenContract.functions.totalSupply().call()
        decimals      = tokenContract.functions.decimals().call()
        totalSupply   = float(totalSupply)/pow(10,decimals)
        symbol        = tokenContract.functions.symbol().call()
        print(symbol , totalSupply)
        return symbol , totalSupply









