from credmark.cmf.model import Model
from credmark.cmf.ipython import create_cmf
from credmark.cmf.types import Address, BlockNumber, Token, Contract 
from credmark.dto import DTO

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
        result = {}
        cmf_param = {
            'chain_id': 1,
        }
        context, _model_loader = create_cmf(cmf_param)
        LineOfCredit = Contract(LocInput.lineOfCreditAddress)
        [interstAccrued, avaialbleCredit, deadline, normalDeadline] = context.web3_batch.call([
            LineOfCredit.functions.interestAccrued(id),
            LineOfCredit.functions.available(id),
            LineOfCredit.functions.deadline(),
            LineOfCredit.functions.arbiter()
        ], unwrap=True)

        return result

