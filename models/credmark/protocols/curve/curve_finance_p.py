import sys
from typing import Any, Dict, List
import time
import credmark.model

from credmark.types import Address
from credmark.types.dto import DTO, DTOField
from ....tmp_abi_lookup import CURVE_SWAP_ABI_1, CURVE_SWAP_ABI_2, CURVE_REGISTRY_ADDRESS, CURVE_REGISTRY_ABI

# from credmark.model import Task, ModelTask, Pipe


class PoolAddress(DTO):
    address: Address = DTOField(..., description='Address of Pool')


@credmark.model.describe(slug="curve-fi-pool-info-p",
                         version="1.0",
                         display_name="Curve Finance Pool Liqudity",
                         description="The amount of Liquidity for Each Token in a Curve Pool",
                         input=PoolAddress)
class CurveFinancePoolInfo(credmark.model.Model):
    def run(self, input: PoolAddress) -> dict:
        pool_address = input.address.checksum


def init_web3(http_provider, block_number, force=False):
    worker = get_worker()
    with worker._lock:
        if not hasattr(worker, "_web3"):
            worker._web3 = {}
            has_web3 = False
        else:
            has_web3 = (http_provider in worker._web3 and
                        block_number in worker._web3[http_provider] and
                        not force)
        if not has_web3:
            web3 = Web3(Web3.HTTPProvider(http_provider))
            web3.eth.default_block = block_number if \
                block_number is not None else 'latest'
            worker._web3[http_provider] = {block_number: {'web3': web3}}
            return True
        else:
            return False


def create_contract(http_provider, block_number, contract_address, contract_abi, force=False):
    worker = get_worker()
    with worker._lock:
        web3_dict = worker._web3[http_provider][block_number]
        web3 = web3_dict['web3']
        if contract_address not in web3_dict or force:
            contract = web3.eth.contract(
                address=web3.toChecksumAddress(contract_address),
                abi=contract_abi)
            worker._web3[http_provider][block_number][contract_address] = contract
            return True
        else:
            return False


def get_contract(http_provider, block_number, contract_address: Address, contract_abi: str):
    worker = get_worker()
    init_web3(http_provider, block_number)
    create_contract(http_provider, block_number, contract_address, contract_abi)
    with worker._lock:
        contract = worker._web3[http_provider][block_number][contract_address]
        return contract


def contract_call_function(http_provider, block_number, contract_address, contract_abi, func_name, *param):
    worker = get_worker()
    init_web3(http_provider, block_number)
    create_contract(http_provider, block_number, contract_address, contract_abi)
    with worker._lock:
        contract = worker._web3[http_provider][block_number][contract_address]
        result = contract.functions[func_name](*param).call()
        return result


def init_web3_contract(http_provider, block_number, contract_address, contract_abi, submit_no):
    new_web3 = init_web3(http_provider, block_number)
    new_contract = create_contract(http_provider, block_number, contract_address, contract_abi)
    worker = get_worker()
    return new_web3, new_contract, submit_no, worker.address, time.time_ns()


def get_pool_info(http_provider, block_number, contract_address, contract_abi, contract_abi2):
    tokens = []
    underlying = []
    balances = []
    init_web3_contract(http_provider, block_number, contract_address, CURVE_SWAP_ABI_1, 0)
    try:
        pool_contract = get_contract(http_provider, block_number, contract_address, contract_abi)
        pool_contract.functions.coins(0).call()
    except Exception:
        pool_contract = get_contract(http_provider, block_number, contract_address, contract_abi2)

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
        "swap_contract_address": contract_address,
        "virtualPrice": virtual_price,
        "tokens": tokens,
        "balances": balances,
        "underlying": underlying,
        "A": a,
    }


def get_all_pool_info(http_provider, block_number, pools, contract_abi, contract_abi2):
    client = get_client()
    params = ([http_provider] * len(pools),
              [block_number] * len(pools),
              pools,
              [contract_abi] * len(pools),
              [contract_abi2] * len(pools))
    fs = client.map(get_pool_info, *params)
    res = client.gather(fs)
    return res

# python test\test.py run -b 14000000 -i '{}' --dask='tcp://localhost:8786' curve-fi-all-pool-info-p
# credmark-dev run curve-fi-all-pool-info -b 14234904 --api_url=http://localhost:8700/v1/model/run -i '{"address":"0x06364f10B501e868329afBc005b3492902d6C763"}'
# python test\test.py run curve-fi-all-pool-info-p -b 14234904 --api_url=http://localhost:8700/v1/model/run -i '{"address":"0x06364f10B501e868329afBc005b3492902d6C763"}' --dask='tcp://localhost:8786'
# Pipe(t1).run(client, ['pool-info'])
# Pipe(t1).run_plain(client, ['pool-info'])


def imp_test():
    import models.credmark
    return models.credmark.__name__


def change_sys():
    import sys
    return sys.path


@credmark.model.describe(slug="curve-fi-all-pool-info-p2",
                         version="1.0",
                         display_name="Curve Finance Pool Liqudity",
                         description="The amount of Liquidity for Each Token in a Curve Pool")
class CurveFinanceTotalTokenLiqudity(credmark.model.Model):

    def run(self, input) -> dict:

        pools = self.context.run_model("curve-fi-pools")['result']

        client.submit(lambda x: models.credmark.protocols.curve.curve_finance_p.imp_test(), 1)
        client.submit(lambda x: change_sys(), 1).result()
        # client.submit(lambda x: imp_test(), 1).result()

        client.submit(lambda x: (sys.path.insert(
            0, sys.path[0] + '\\models_pkg.zip'), sys.path, reload_models(models), models.__path__), 1).result()

        t1 = Task('pool-info', get_all_pool_info, input=(
            [self.context.dask_client.web3_http_provider, self.context.dask_client.block_number, pools, CURVE_SWAP_ABI_1, CURVE_SWAP_ABI_2], []))
        breakpoint()

        client.submit({'out': reload_models(models)}, ['out'])

        client.get({'out': t1()}, ['out'])
        pool_infos = self.context.run_pipe(Pipe(t1), ['pool-info'])
        Pipe(t1).run_plain(client, ['pool-info'])
        breakpoint()
        return {"pools": pool_infos}


@credmark.model.describe(slug="curve-fi-pools-p2",
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
