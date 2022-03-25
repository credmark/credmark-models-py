from typing import Any, List
import credmark.model
from credmark.types import Address, Account
from credmark.dto import IterableListGenericDTO, DTOField, PrivateAttr
from credmark.types.data.data_content.fungible_token_data import FUNGIBLE_TOKEN_DATA


class LabeledAccount(Account):
    label: str


class LabeledAccounts(IterableListGenericDTO[LabeledAccount]):
    accounts: List[LabeledAccount] = DTOField(
        default=[], description="A list of Labeled Accounts"
    )
    _iterator: str = PrivateAttr('accounts')
    _attribute: str = PrivateAttr('label')

    def __getattribute__(self, __name: str) -> Any:
        try:
            return super().__getattribute__(__name)
        except AttributeError:
            for account in self.accounts:
                if account.label == __name:
                    return account


@credmark.model.describe(slug='example.labeled-accounts-outer',
                         version='1.0',
                         output=LabeledAccounts)
class ExampleLabeledAccountsOuter(credmark.model.Model):
    def run(self, input: LabeledAccounts) -> LabeledAccounts:

        return self.context.models.example.labeled_accounts_inner(input=LabeledAccounts(accounts=[
            LabeledAccount(label=t['symbol'], address=t.get('address', Address.null())) for t in FUNGIBLE_TOKEN_DATA[str(self.context.chain_id)]
        ]), return_type=LabeledAccounts)


@credmark.model.describe(slug='example.labeled-accounts-inner',
                         version='1.0',
                         input=LabeledAccounts)
class ExampleLabeledAccountsInner(credmark.model.Model):
    def run(self, input: LabeledAccounts) -> LabeledAccounts:

        self.logger.info(f'input.USDC : {input.USDC}')
        return input
