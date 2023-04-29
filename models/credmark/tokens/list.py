# pylint: disable=locally-disabled, no-member

from credmark.cmf.model import Model
from credmark.cmf.types import Records
from credmark.cmf.types.data.fungible_token_data import FUNGIBLE_TOKEN_DATA_BY_SYMBOL
from credmark.dto import EmptyInput


@Model.describe(slug='token.list',
                version='0.2',
                display_name='List of non-scam tokens',
                description='The current Credmark supported list to value account',
                category='token',
                tags=['token'],
                output=Records)
class TokenList(Model):
    def run(self, _: EmptyInput) -> Records:
        existing_tokens = [
            (v['address'], v['symbol'], v['name'], v['decimals'])
            for v in FUNGIBLE_TOKEN_DATA_BY_SYMBOL[self.context.chain_id].values()]
        rec = Records(records=existing_tokens,
                      fields=['address', 'symbol', 'name', 'decimals'],
                      n_rows=len(existing_tokens),
                      fix_int_columns=[])
        return rec
