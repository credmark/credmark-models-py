from datetime import datetime
from typing import List

from requests.exceptions import ReadTimeout
from urllib3.exceptions import ReadTimeoutError
from web3._utils.events import get_event_data
from web3._utils.filters import construct_event_filter_params

from credmark.cmf.model import Model
from credmark.cmf.model.errors import (ModelDataError, ModelRunError,
                                       create_instance_from_error_dict)
from credmark.cmf.types import (Account, Accounts, Contract, ContractLedger,
                                Contracts, Price, Token)
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO, EmptyInput


class VestingInfo(DTO):
    account: Account
    vesting_contract: Contract
    vesting_start_datetime: str
    vesting_end_datetime: str
    vested_amount: float
    unvested_amount: float
    claimable_amount: float
    claimed_amount: float


class AccountVestingInfo(DTO):
    account: Account
    vesting_infos: List[VestingInfo]
    claims: List[dict]


@Model.describe(
    slug="cmk.vesting-contracts",
    version="1.0",
    display_name='CMK Vesting Contracts',
    category='protocol',
    subcategory='cmk',
    input=EmptyInput,
    output=Contracts)
class CMKGetVestingContracts(Model):
    def run(self, input) -> Contracts:
        if self.context.chain_id == 1:
            return Contracts(
                contracts=[
                    Contract(address="0xCbF507C87f19B58fB719B65697Fb7fA84D682aA9"),
                    Contract(address="0x46d812De7EF3cA2E3c1D8EfFb496F070b2202DFF"),
                    Contract(address="0xCA9bb8A10B2C0FB16A18eDae105456bf7e91B041"),
                    Contract(address="0x70371C6D23A26Df7Bf0654C47D69ddE9000013E7"),
                    Contract(address="0x0f8d3D79f5Fb9EDFceFF399F056c996eb9b89C67"),
                    Contract(address="0xC2560D7D2cF12f921193874cc8dfBC4bb162b7cb"),
                    Contract(address="0xdb9DCecbA3f21e2aa53897a05A92F89209731b68"),
                    Contract(address="0x5CE367c907a119afa25f4DBEe4f5B4705C802Df5"),
                ]
            )
        raise ModelDataError(message="cmk vesting contracts only deployed on mainnet",
                             code=ModelDataError.Codes.NO_DATA)


@Model.describe(
    slug="cmk.get-vesting-accounts",
    version="1.0",
    display_name='CMK Vesting Accounts',
    category='protocol',
    subcategory='cmk',
    input=EmptyInput,
    output=Accounts
)
class CMKGetVestingAccounts(Model):
    def run(self, input) -> Accounts:
        accounts = set()
        accounts_info = []
        for c in Contracts(**self.context.models.cmk.vesting_contracts()):
            try:
                vesting_added_events = c.events.VestingScheduleAdded.createFilter(
                    fromBlock=0,
                    toBlock=self.context.block_number
                ).get_all_entries()
            except ValueError:
                # Some Eth node does not support the newer eth_newFilter method
                try:
                    # pylint:disable=locally-disabled,protected-access
                    event_abi = c.instance.events.VestingScheduleAdded._get_event_abi()

                    __data_filter_set, event_filter_params = construct_event_filter_params(
                        abi_codec=self.context.web3.codec,
                        event_abi=event_abi,
                        address=c.address.checksum,
                        fromBlock=0,
                        toBlock=self.context.block_number
                    )
                    vesting_added_events = self.context.web3.eth.get_logs(event_filter_params)
                    vesting_added_events = [get_event_data(self.context.web3.codec, event_abi, s)
                                            for s in vesting_added_events]
                except (ReadTimeoutError, ReadTimeout):
                    raise ModelRunError(
                        f'There was timeout error when reading logs for {c.address}')
            for vae in vesting_added_events:
                if vae['args']['account'] not in accounts:
                    accounts.add(vae['args']['account'])
                    accounts_info.append(Account(address=vae['args']['account']))

        return Accounts(accounts=accounts_info)


@Model.describe(
    slug="cmk.get-vesting-info-by-account",
    version="1.1",
    display_name='CMK Vesting Info by Account',
    category='protocol',
    subcategory='cmk',
    input=Account,
    output=AccountVestingInfo)
class CMKGetVestingByAccount(Model):
    def run(self, input: Account) -> AccountVestingInfo:
        vesting_contracts = Contracts(**self.context.models.cmk.vesting_contracts())
        result = AccountVestingInfo(account=input, vesting_infos=[], claims=[])
        token = Token(symbol="CMK")
        claims = []
        current_price = Price(**self.context.models.uniswap_v3.get_weighted_price(
            input={"symbol": "CMK"})).price
        for vesting_contract in vesting_contracts:
            if vesting_contract.functions.getElapsedVestingTime(input.address).call() == 0:
                continue
            vesting_info = VestingInfo(
                account=input,
                vesting_contract=vesting_contract,
                vesting_start_datetime=str(
                    datetime.fromtimestamp(
                        self.context.block_number.timestamp -
                        vesting_contract.functions.getElapsedVestingTime(
                            input.address).call())),
                vesting_end_datetime=str(
                    datetime.fromtimestamp(
                        vesting_contract.functions.getVestingMaturationTimestamp(
                            input.address).call())),
                vested_amount=token.scaled(
                    vesting_contract.functions.getVestedAmount(input.address).call()),
                unvested_amount=token.scaled(
                    vesting_contract.functions.getUnvestedAmount(input.address).call()),
                claimable_amount=token.scaled(
                    vesting_contract.functions.getClaimableAmount(input.address).call()
                ),
                claimed_amount=token.scaled(
                    vesting_contract.functions.getVestedAmount(input.address).call() -
                    vesting_contract.functions.getClaimableAmount(input.address).call()
                ))
            result.vesting_infos.append(vesting_info)

            try:
                allocation_claimed_events = vesting_contract.events.AllocationClaimed.createFilter(
                    fromBlock=0, toBlock=self.context.block_number).get_all_entries()
            except ValueError:
                try:
                    # pylint:disable=locally-disabled,protected-access
                    event_abi = vesting_contract.events.AllocationClaimed._get_event_abi()

                    __data_filter_set, event_filter_params = construct_event_filter_params(
                        abi_codec=self.context.web3.codec,
                        event_abi=event_abi,
                        address=input.address.checksum,
                        fromBlock=0,
                        toBlock=self.context.block_number
                    )
                    allocation_claimed_events = self.context.web3.eth.get_logs(event_filter_params)
                    allocation_claimed_events = [
                        get_event_data(self.context.web3.codec, event_abi, s)
                        for s in allocation_claimed_events]
                except (ReadTimeoutError, ReadTimeout):
                    raise ModelRunError(
                        f'There was timeout error when reading logs for {input.address}')

            claims_all = [dict(d['args']) for d in allocation_claimed_events]

            for c in claims_all:
                if c['account'] == input.address:
                    c['amount'] = Token(symbol="CMK").scaled(c['amount'])
                    c['value_at_claim_time'] = c['amount'] * self.context.run_model(
                        slug="uniswap-v3.get-weighted-price",
                        input={"symbol": "CMK"},
                        block_number=self.context.block_number.from_timestamp(c['timestamp']),
                        return_type=Price).price
                    c['value_now'] = c['amount'] * current_price
                    claims.append(c)

            # TODO: New ledger based model, unused due to L2 performance.

            def _new_ledger_based_model(vesting_contract):
                _input_address = input.address
                assert vesting_contract.abi is not None
                cols = vesting_contract.abi.events.AllocationClaimed.args
                ledger_events = (
                    vesting_contract.ledger.events.AllocationClaimed(
                        columns=[ContractLedger.Events.InputCol(c) for c in cols],
                        order_by=ContractLedger.Events.InputCol("account"),
                        limit="5000")
                    .to_dataframe()
                    .query('inp_account == @_input_address'))

                def price_at_claim_time(row, self=self):
                    timestamp = row['inp_timestamp']
                    price = self.context.run_model(
                        slug="uniswap-v3.get-weighted-price",
                        input={"symbol": "CMK"},
                        block_number=self.context.block_number.from_timestamp(timestamp),
                        return_type=Price).price
                    return price

                if not ledger_events.empty:
                    ledger_events.loc[:, 'amount_scaled'] = (
                        ledger_events.inp_amount.apply(Token(symbol="CMK").scaled))
                    ledger_events.loc[:, 'price_now'] = current_price
                    ledger_events.loc[:, 'value_now'] = current_price * ledger_events.amount_scaled
                    ledger_events.loc[:, 'price_at_claim_time'] = (
                        ledger_events.apply(price_at_claim_time, axis=1))
                    ledger_events.loc[:, 'value_at_claim_time'] = (
                        ledger_events.price_at_claim_time * ledger_events.amount_scaled)

                    for _, r in ledger_events.iterrows():
                        claim = {
                            'account': r['inp_account'],
                            'amount': r['inp_amount'],
                            'timestamp': r['inp_timestamp'],
                            'amount_scaled': r['amount_scaled'],
                            'value_at_claim_time': r['value_at_claim_time'],
                            'value_now': r['value_now'],
                            'price_at_claim_time': r['price_at_claim_time'],
                            'price_now': r['price_now'],
                        }
                        claims.append(claim)

        result.claims = claims

        return result


@Model.describe(
    slug="cmk.get-all-vesting-balances",
    version="1.1",
    display_name='CMK Vesting Balances',
    category='protocol',
    subcategory='cmk',
    input=EmptyInput,
    output=dict)
class CMKGetAllVestingBalances(Model):
    def run(self, input: EmptyInput) -> dict:
        accounts = Accounts(**self.context.models.cmk.get_vesting_accounts())

        def _use_for():
            results = {"vesting_infos": []}
            for account in accounts:
                results['vesting_infos'].append(
                    self.context.models.cmk.get_vesting_info_by_account(account)
                )
            return results

        def _use_compose():
            model_slug = 'cmk.get-vesting-info-by-account'
            model_inputs = accounts

            accounts_run = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': model_slug, 'modelInputs': model_inputs.accounts},
                return_type=MapInputsOutput[Account, dict])

            results = {"vesting_infos": []}
            for p in accounts_run:
                if p.output is not None:
                    results['vesting_infos'].append(p.output)
                elif p.error is not None:
                    self.logger.error(p.error)
                    raise create_instance_from_error_dict(p.error.dict())
                else:
                    raise ModelRunError('compose.map-inputs: output/error cannot be both None')
            return results

        results = _use_compose()
        return results


@Model.describe(
    slug="cmk.vesting-events",
    version="1.0",
    display_name='CMK Vesting Events',
    category='protocol',
    subcategory='cmk',
    input=Contract,
    output=dict
)
class CMKVestingEvents(Model):
    def run(self, input: Contract) -> dict:
        try:
            allocation_claimed_events = input.events.AllocationClaimed.createFilter(
                fromBlock=0, toBlock=self.context.block_number).get_all_entries()
        except ValueError:
            # Some Eth node does not support the newer eth_newFilter method
            try:
                # pylint:disable=locally-disabled,protected-access
                event_abi = input.instance.events.AllocationClaimed._get_event_abi()

                __data_filter_set, event_filter_params = construct_event_filter_params(
                    abi_codec=self.context.web3.codec,
                    event_abi=event_abi,
                    address=input.address.checksum,
                    fromBlock=0,
                    toBlock=self.context.block_number
                )
                allocation_claimed_events = self.context.web3.eth.get_logs(event_filter_params)
                allocation_claimed_events = [get_event_data(self.context.web3.codec, event_abi, s)
                                             for s in allocation_claimed_events]
            except (ReadTimeoutError, ReadTimeout):
                raise ModelRunError(
                    f'There was timeout error when reading logs for {input.address}')

        claims = [dict(d['args']) for d in allocation_claimed_events]

        # cancels = [
        #     dict(d['args']) for d in
        #     input.events.VestingScheduleCanceled.createFilter(
        #     fromBlock=0,
        #     toBlock=self.context.block_number
        #     ).get_all_entries()]

        return {"events": claims}
