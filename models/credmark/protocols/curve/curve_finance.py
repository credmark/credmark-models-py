import credmark.model

from credmark.types import Address
from credmark.types.dto import DTO, DTOField
from ....tmp_abi_lookup import SWAP_ABI, SWAP_AB2, CURVE_REGISTRY_ADDRESS, CURVE_REGISTRY_ABI

# Demo use of


class PoolAddress(DTO):
    address: Address = DTOField(..., description='Address of Pool')


@credmark.model.describe(slug="curve-fi-pool-info",
                         version="1.0",
                         display_name="Curve Finance Pool Liqudity",
                         description="The amount of Liquidity for Each Token in a Curve Pool",
                         input=PoolAddress)
class CurveFinancePoolInfo(credmark.model.Model):

    def run(self, input: PoolAddress) -> dict:
        pool_address = input.address
        pool_contract = self.context.web3.eth.contract(
            address=pool_address.checksum,
            abi=SWAP_ABI
        )
        tokens = []
        underlying = []
        balances = []
        try:
            pool_contract.functions.coins(0).call()
        except Exception:
            pool_contract = self.context.web3.eth.contract(
                address=input.address.checksum,
                abi=SWAP_AB2
            )
        for i in range(0, 8):
            try:
                tok = pool_contract.functions.coins(i).call()
                bal = pool_contract.functions.balances(i).call()
                try:
                    und = pool_contract.functions.underlying_coins(i).call()
                    underlying.append(und)
                except Exception:
                    pass
                balances.append(bal)
                tokens.append(tok)
            except Exception:
                break

        virtual_price = pool_contract.functions.get_virtual_price().call()
        a = pool_contract.functions.A().call()

        return {
            "swap_contract_address": pool_address,
            "virtualPrice": virtual_price,
            "tokens": tokens,
            "balances": balances,
            "underlying": underlying,
            "A": a,
        }


@credmark.model.describe(slug="curve-fi-all-pool-info",
                         version="1.0",
                         display_name="Curve Finance Pool Liqudity",
                         description="The amount of Liquidity for Each Token in a Curve Pool")
class CurveFinanceTotalTokenLiqudity(credmark.model.Model):

    def run(self, input) -> dict:
        pool_infos = []
        for pool in self.context.run_model("curve-fi-pools")['result'][:3]:

            pool_info = self.context.run_model(
                "curve-fi-pool-info", {"address": pool})
            pool_infos.append(pool_info)
        return {"pools": pool_infos}


@credmark.model.describe(slug="curve-fi-pools",
                         version="1.0",
                         display_name="Curve Finance Pool Liqudity",
                         description="The amount of Liquidity for Each Token in a Curve Pool")
class CurveFinancePools(credmark.model.Model):

    def run(self, input) -> dict:
        registry = self.context.web3.eth.contract(
            address=Address(CURVE_REGISTRY_ADDRESS).checksum,
            abi=CURVE_REGISTRY_ABI)

        total_pools = registry.functions.pool_count().call()
        pool_addresses = []
        for i in range(0, total_pools):
            pool_addresses.append(registry.functions.pool_list(i).call())
        return {'result': pool_addresses}
