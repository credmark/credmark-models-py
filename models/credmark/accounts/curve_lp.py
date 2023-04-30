
import numpy as np
from credmark.cmf.model import Model
from credmark.cmf.types import (
    Account,
    Accounts,
    Address,
    Contract,
    Network,
    Portfolio,
    Position,
    Records,
    Token,
    TokenPosition,
    Tokens,
)


class CurveLPPosition(Position):
    pool: Contract
    supply_position: Portfolio
    lp_position: Portfolio


@Model.describe(slug="curve.lp-accounts",
                version="1.5",
                display_name="Accounts position in Curve LP",
                description="All the positions in Curve LP",
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['curve'],
                input=Accounts,
                output=Portfolio)
class GetCurveLPPositionAccounts(Model):
    def run(self, input: Accounts) -> Portfolio:
        port = Portfolio()
        for acc in input:
            p2 = self.context.run_model('curve.lp',
                                        input=acc,
                                        return_type=Portfolio)
            port = Portfolio.merge(port, p2)
        return port


@Model.describe(slug="curve.lp",
                version="1.6",
                display_name="Account position in Curve LP",
                description="All the positions in Curve LP",
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['curve'],
                input=Account,
                output=Portfolio)
class GetCurveLPPosition(Model):
    CURVE_LP_TOKEN = {
        Network.Mainnet: {
            Address('0xc4ad29ba4b3c580e6d59105fff484999997675ff')
        }
    }

    def run(self, input: Account) -> Portfolio:
        df = (self.context.run_model('account.token-transfer',
                                     input=input,
                                     return_type=Records)
              .to_dataframe())

        _lp_tokens = self.CURVE_LP_TOKEN[self.context.network]
        lp_tx = df.query('token_address in @_lp_tokens')

        txs = lp_tx.transaction_hash.unique().tolist()
        lp_position = []
        for _tx in txs:
            df_tx = df.query('transaction_hash == @_tx')
            if df_tx.shape[0] == 2:
                tx_in = df_tx.query('token_address not in @_lp_tokens')
                in_token = Token(address=tx_in['token_address'].iloc[0])
                in_token_amount = in_token.scaled(tx_in['value'].iloc[0])
                if tx_in['from_address'].iloc[0] == input.address:
                    in_token_amount = abs(in_token_amount)
                else:
                    in_token_amount = -abs(in_token_amount)

                tx_out = df_tx.query('token_address in @_lp_tokens')
                lp_token = Token(address=tx_out['token_address'].iloc[0])
                lp_token_amount = tx_out['value'].iloc[0]
                _lp_token_amount_scaled = lp_token.scaled(lp_token_amount)
                if tx_in['from_address'].iloc[0] == input.address:
                    lp_token_amount = abs(lp_token_amount)
                else:
                    lp_token_amount = -abs(lp_token_amount)

                pool_info = self.context.run_model(
                    'curve-fi.pool-info', lp_token)
                pool_contract = Contract(address=pool_info['address'])
                pool_tokens = Tokens(**pool_info['tokens'])
                withdraw_token_amount = np.zeros(len(pool_tokens.tokens))
                np_balances = np.array(pool_info['balances'])
                for tok_n, tok in enumerate(pool_tokens):
                    withdraw_one = [0] * len(pool_tokens.tokens)
                    withdraw_one[tok_n] = 1
                    withdraw_token_amount[tok_n] = pool_contract.functions.calc_token_amount(
                        withdraw_one, False).call()
                    np_balances[tok_n] = np_balances[tok_n] / \
                        pool_tokens[tok_n].scaled(1)

                for tok_n, tok in enumerate(pool_tokens.tokens):
                    ratio = np_balances.dot(
                        withdraw_token_amount) / np_balances[tok_n]
                    amount = lp_token_amount / ratio
                    lp_position.append(
                        Position(
                            asset=tok,
                            amount=pool_tokens[tok_n].scaled(amount)))

                _ = CurveLPPosition(
                    asset=lp_token,
                    amount=_lp_token_amount_scaled,
                    pool=Contract(address=lp_token.functions.minter().call()),
                    supply_position=Portfolio(
                        positions=[TokenPosition(asset=in_token,
                                                 amount=in_token_amount)]),
                    lp_position=Portfolio(positions=lp_position))

        return Portfolio.merge(Portfolio(positions=lp_position),
                               Portfolio(positions=[]))
