from credmark.cmf.model import Model
from credmark.cmf.ipython import create_cmf
from credmark.cmf.types import Address, BlockNumber, Token, Contract 
from models.tmp_abi_lookup import ESCROW, RAIN_LOC
from credmark.dto import DTO
import datetime
# credmark-dev run <model-name> -i {"contract_address":"address"} -j -c 1 -b latest

class LocInput(DTO):
    lineOfCreditAddress: Address

@Model.describe(
    slug='contrib.credit-coop-line-of-credit',
    version='1.0',
    display_name='Line of Credit',
    description='Tracks credit line data.',
    category='protocol',
    tags=['credit'],
    input=LocInput,
    output=dict
)
class LineOfCredit(Model):
    def run(self, input: LocInput) -> dict:
        
        LineOfCredit = Contract(input.lineOfCreditAddress).set_abi(RAIN_LOC, set_loaded=True)
        escrow = LineOfCredit.functions.escrow().call()
        escrowContract = Contract(escrow).set_abi(ESCROW, set_loaded=True)
        id = LineOfCredit.functions.ids(0).call()
        
        [interstAccrued, avaialbleCredit, deadline, collateral, credit] = self.context.web3_batch.call([
            LineOfCredit.functions.interestAccrued(id),
            LineOfCredit.functions.available(id),
            LineOfCredit.functions.deadline(),
            escrowContract.functions.getCollateralValue(),
            LineOfCredit.functions.credits(id)
        ], unwrap=True)

        normalDeadline = datetime.datetime.fromtimestamp(deadline, datetime.UTC)
        token = Token(credit[5])
        symbol = token.symbol

        token_price = self.context.run_model(
                    slug='price.quote',
                    input={'base': token})['price']

        return {
            f'Interest Accrued ({symbol}): ': (interstAccrued / 10**credit[4]) * token_price,
            f'Outstanding Principal ({symbol}): ': (credit[1] / 10**credit[4]) * token_price,
            f'Total Outsanding Debt ({symbol}): ': ((credit[1] + interstAccrued) / 10**credit[4]) * token_price,
            f'Funds Available to Drawdown ({symbol}): ': (avaialbleCredit[0] / 10**credit[4]) * token_price,
            f'Interest Available to Withdraw ({symbol}): ': (avaialbleCredit[1]/(10**credit[4])) * token_price,
            'Deadline: ': normalDeadline,
            'Collateral Value (USD): ': collateral,
        }