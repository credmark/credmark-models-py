from typing import List
from credmark.cmf.model import Model, describe
from credmark.cmf.types import Contract, Contracts, Account, Token, Accounts
from credmark.dto import EmptyInput, DTO
from credmark.cmf.model.errors import ModelDataError
from datetime import datetime

from credmark.cmf.model.errors import (
    ModelRunError,
)

from web3._utils.filters import construct_event_filter_params
from web3._utils.events import get_event_data
from urllib3.exceptions import ReadTimeoutError
from requests.exceptions import ReadTimeout


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


@describe(
    slug="cmk.vesting-contracts",
    version="1.0",
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
        raise ModelDataError(message="cmk vesting contracts only deployed on mainnet")


@describe(
    slug="cmk.get-vesting-accounts",
    version="1.0",
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


@describe(
    slug="cmk.get-vesting-info-by-account",
    version="1.0",
    input=Account,
    output=AccountVestingInfo)
class CMKGetVestingByAccount(Model):
    def run(self, input: Account) -> AccountVestingInfo:
        vesting_contracts = Contracts(**self.context.models.cmk.vesting_contracts())
        result = AccountVestingInfo(account=input, vesting_infos=[])
        token = Token(symbol="CMK")
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
        return result


@describe(
    slug="cmk.get-all-vesting-balances",
    version="1.0",
    input=EmptyInput,
    output=dict)
class CMKGetAllVestingBalances(Model):
    def run(self, input: EmptyInput) -> dict:
        accounts = Accounts(**self.context.models.cmk.get_vesting_accounts())
        results = {"vesting_infos": []}
        for account in accounts:
            results['vesting_infos'].append(
                self.context.models.cmk.get_vesting_info_by_account(account))
        return results


@describe(
    slug="cmk.vesting-events",
    version="1.0",
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
