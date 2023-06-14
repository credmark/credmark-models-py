from datetime import datetime
from typing import List

from credmark.cmf.model import Model
from credmark.cmf.model.errors import (
    ModelDataError,
    ModelRunError,
    create_instance_from_error_dict,
)
from credmark.cmf.types import (
    Account,
    Accounts,
    Contract,
    Contracts,
    PriceWithQuote,
    Token,
)
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO


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


@Model.describe(slug="cmk.vesting-contracts",
                version="1.0",
                display_name='CMK Vesting Contracts',
                category='protocol',
                subcategory='cmk',
                output=Contracts)
class CMKGetVestingContracts(Model):
    def run(self, _) -> Contracts:
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


@Model.describe(slug="cmk.get-vesting-accounts",
                version="1.3",
                display_name='CMK Vesting Accounts',
                category='protocol',
                subcategory='cmk',
                output=Accounts)
class CMKGetVestingAccounts(Model):
    def run(self, _) -> Accounts:
        accounts = set()
        accounts_info = []

        vesting_contracts = self.context.run_model('cmk.vesting-contracts',
                                                   {},
                                                   return_type=Contracts)
        for contract in vesting_contracts:
            with contract.ledger.events.VestingScheduleAdded as q:
                ledger_events = q.select(columns=q.columns,
                                         order_by=q.EVT_ACCOUNT,
                                         limit=5000)

            for evt in ledger_events:
                acc = evt['evt_account']
                if acc not in accounts:
                    accounts.add(acc)
                    accounts_info.append(Account(address=acc))

        return Accounts(accounts=accounts_info)


class CredmarkVestingAccount(Account):
    class Config:
        schema_extra = {
            'example': {"address": "0xd766ee3ab3952fe7846db899ce0139da06fbe459"}
        }


@Model.describe(slug="cmk.get-vesting-info-by-account",
                version="1.7",
                display_name='CMK Vesting Info by Account',
                category='protocol',
                subcategory='cmk',
                input=CredmarkVestingAccount,
                output=AccountVestingInfo)
class CMKGetVestingByAccount(Model):

    def get_vesting_info(self,
                         token: Token,
                         vesting_contract: Contract,
                         account: Account):
        functions = vesting_contract.functions
        elapsed_vesting_time = functions.getElapsedVestingTime(account.address).call()
        if elapsed_vesting_time == 0:
            return None

        return VestingInfo(
            account=account,
            vesting_contract=vesting_contract,
            vesting_start_datetime=str(datetime.fromtimestamp(
                self.context.block_number.timestamp - elapsed_vesting_time)),
            vesting_end_datetime=str(datetime.fromtimestamp(
                functions.getVestingMaturationTimestamp(account.address).call())),
            vested_amount=token.scaled(functions.getVestedAmount(account.address).call()),
            unvested_amount=token.scaled(functions.getUnvestedAmount(account.address).call()),
            claimable_amount=token.scaled(functions.getClaimableAmount(account.address).call()),
            claimed_amount=token.scaled(
                vesting_contract.functions.getVestedAmount(account.address).call() -
                vesting_contract.functions.getClaimableAmount(account.address).call()
            ))

    def get_claims(self,
                   token: Token,
                   vesting_contract: Contract,
                   account: Account,
                   current_price: float):
        assert vesting_contract.abi is not None
        with vesting_contract.ledger.events.AllocationClaimed as q:
            ledger_events = q.select(
                columns=q.columns,
                order_by=q.EVT_ACCOUNT,
                where=q.EVT_ACCOUNT.eq(account.address),
                limit=5000).to_dataframe()

        def price_at_claim_time(row, self=self):
            timestamp = row['evt_timestamp']
            price = self.context.run_model(
                slug="price.quote",
                input={"base": "CMK"},
                block_number=self.context.block_number.from_timestamp(
                    timestamp),
                return_type=PriceWithQuote).price
            return price

        if ledger_events.empty:
            return []

        ledger_events.loc[:, 'amount_scaled'] = (
            ledger_events['evt_amount'].apply(token.scaled))
        ledger_events.loc[:, 'price_now'] = current_price
        ledger_events.loc[:, 'value_now'] = current_price * ledger_events.amount_scaled
        ledger_events.loc[:, 'price_at_claim_time'] = (
            ledger_events.apply(price_at_claim_time, axis=1))
        ledger_events.loc[:, 'value_at_claim_time'] = (
            ledger_events.price_at_claim_time * ledger_events.amount_scaled)

        claims = []
        for _, r in ledger_events.iterrows():
            claims.append({
                'account': r['evt_account'],
                'amount': r['evt_amount'],
                'timestamp': r['evt_timestamp'],
                'amount_scaled': r['amount_scaled'],
                'value_at_claim_time': r['value_at_claim_time'],
                'value_now': r['value_now'],
                'price_at_claim_time': r['price_at_claim_time'],
                'price_now': r['price_now'],
            })

        return claims

    def run(self, input: Account) -> AccountVestingInfo:
        vesting_contracts = self.context.run_model('cmk.vesting-contracts',
                                                   {},
                                                   return_type=Contracts)
        result = AccountVestingInfo(account=input, vesting_infos=[], claims=[])
        token = Token(symbol="CMK")

        current_price = self.context.run_model('price.quote',
                                               {"base": "CMK"},
                                               return_type=PriceWithQuote).price

        for vesting_contract in vesting_contracts:
            vesting_info = self.get_vesting_info(token, vesting_contract, input)
            if vesting_info is None:
                continue

            claims = self.get_claims(token, vesting_contract, input, current_price)

            result.vesting_infos.append(vesting_info)
            result.claims.extend(claims)

        return result


@Model.describe(slug="cmk.get-all-vesting-balances",
                version="1.1",
                display_name='CMK Vesting Balances',
                category='protocol',
                subcategory='cmk',
                output=dict)
class CMKGetAllVestingBalances(Model):
    def run(self, _) -> dict:
        accounts = Accounts(**self.context.models.cmk.get_vesting_accounts())

        def _use_for():
            results = {"vesting_infos": []}
            for account in accounts:
                results['vesting_infos'].append(
                    self.context.models.cmk.get_vesting_info_by_account(
                        account)
                )
            return results

        def _use_compose():
            model_slug = 'cmk.get-vesting-info-by-account'
            model_inputs = accounts

            accounts_run = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': model_slug,
                       'modelInputs': model_inputs.accounts},
                return_type=MapInputsOutput[Account, dict])

            results = {"vesting_infos": []}
            for p in accounts_run:
                if p.output is not None:
                    results['vesting_infos'].append(p.output)
                elif p.error is not None:
                    self.logger.error(p.error)
                    raise create_instance_from_error_dict(p.error.dict())
                else:
                    raise ModelRunError(
                        'compose.map-inputs: output/error cannot be both None')
            return results

        results = _use_compose()
        return results


@Model.describe(slug="cmk.vesting-events",
                version="1.5",
                display_name='CMK Vesting Events',
                category='protocol',
                subcategory='cmk',
                output=dict)
class CMKVestingEvents(Model):
    def run(self, _) -> dict:
        vesting_contracts = self.context.run_model('cmk.vesting-contracts',
                                                   {},
                                                   return_type=Contracts)
        claims = []
        for contract in vesting_contracts:
            with contract.ledger.events.AllocationClaimed as q:
                ledger_events = (q.select(
                    columns=q.columns,
                    order_by=q.EVT_ACCOUNT,
                    limit=5000))
                claims.extend(ledger_events.data)
        return {"events": claims}
