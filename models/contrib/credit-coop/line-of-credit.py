from credmark.cmf.model import Model
from credmark.cmf.ipython import create_cmf
from credmark.cmf.types import Address, BlockNumber, Token, Contract 
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
        
     
        LineOfCredit = Contract(input.lineOfCreditAddress)
        escrow = LineOfCredit.functions.escrow().call()
        escrowContract = Contract(escrow)
        id = LineOfCredit.functions.ids(0)
        

        [interstAccrued, avaialbleCredit, deadline, collateral, credit, token_price] = self.context.web3_batch.call([
            LineOfCredit.functions.interestAccrued(id),
            LineOfCredit.functions.available(id),
            LineOfCredit.functions.deadline(),
            escrowContract.functions.collateral(),
            LineOfCredit.functions.credits(id)
        ], unwrap=True)

        normalDeadline = datetime.datetime.fromtimestamp(deadline, datetime.UTC)
        token = Token(credit[5])

        token_price = self.context.run_model(
                    slug='price.quote',
                    input={'base': token})['price']


        return {
            'interestAccrued': (interstAccrued / 10**credit[4]) * token_price,
            'princeipal outstanding': (credit[1] / 10**credit[4]) * token_price,
            'outsanding debt total': ((credit[1] + interstAccrued) / 10**credit[4]) * token_price,
            'available to drawdown': (avaialbleCredit[0] / 10**credit[4]) * token_price,
            'interest to withdraw': (avaialbleCredit[1]/(10**credit[4])) * token_price,
            'deadline': normalDeadline,
            'collateral': collateral,
        }
    

