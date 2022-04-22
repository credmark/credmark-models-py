from typing import List
from credmark.cmf.model import Model, describe
from credmark.cmf.types import Contract, Contracts, Account, Token, Accounts, Price
from credmark.dto import EmptyInput, DTO
from credmark.cmf.model.errors import ModelDataError
from datetime import datetime

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
        accounts=[]
        for c in Contracts(**self.context.models.cmk.vesting_contracts()):
            vesting_added_events = c.events.VestingScheduleAdded.createFilter(
                fromBlock=0,
                toBlock=self.context.block_number
                ).get_all_entries()
            for vae in vesting_added_events:
                if vae['args']['account'] not in accounts:
                    accounts.append(vae)
        return Accounts(accounts=accounts)

@describe(
    slug="cmk.get-vesting-info-by-account",
    version="1.0",
    input=Account,
    output=AccountVestingInfo)
class CMKGetVestingByAccount(Model):
    def run(self, input: Account) -> AccountVestingInfo:
        vesting_contracts = Contracts(**self.context.models.cmk.vesting_contracts())
        result = AccountVestingInfo(account=input, vesting_infos=[], claims=[])
        token = Token(symbol="CMK")
        claims = []
        current_price = Price(**self.context.models.uniswap_v3.get_average_price(
                        input={"symbol":"CMK"})).price
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
            claims_all= [
                dict(d['args']) for d in
                vesting_contract.events.AllocationClaimed.createFilter(
                    fromBlock=0, toBlock=self.context.block_number
                    ).get_all_entries()]
            for c in claims_all:
                if c['account'] == input.address:
                    c['amount'] = Token(symbol="CMK").scaled(c['amount'])
                    c['value_at_claim_time'] = c['amount'] * self.context.run_model(
                        slug="uniswap-v3.get-average-price",
                        input={"symbol":"CMK"},
                        block_number=self.context.block_number.from_timestamp(c['timestamp']),
                        return_type=Price).price
                    c['value_now'] = c['amount'] * current_price
                    claims.append(c)
        result.claims = claims
        
        return result


@describe(
    slug="cmk.get-all-vesting-balances",
    version="1.0",
    input=EmptyInput,
    output=dict)
class CMKGetAllVestingBalances(Model):
    def run(self, input: EmptyInput) -> dict:
        accounts = Accounts(**self.context.models.cmk.get_vesting_accounts())
        results = {"vesting_infos":[]}
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
    def run(self, input:Contract) -> dict:
        claims= [
            dict(d['args']) for d in
            input.events.AllocationClaimed.createFilter(
                fromBlock=0, toBlock=self.context.block_number
                ).get_all_entries()]
        # cancels = [
        #     dict(d['args']) for d in
        #     input.events.VestingScheduleCanceled.createFilter(
        #     fromBlock=0,
        #     toBlock=self.context.block_number
        #     ).get_all_entries()]

        return {"events":claims}
