# pylint:disable=locally-disabled,line-too-long
from credmark.cmf.model import Model

from credmark.cmf.types import (
    Token
)

"""
credmark-dev run finance.run-model-bug --input '{}' -l finance.var-engine,finance.var-reference,token.price-ext,finance.get-one,uniswap-v2.get-average-price,uniswap-v3.get-average-price,sushiswap.get-average-price -b 14234904 --format_json
"""


@Model.describe(slug='finance.sub-model-bug',
                version='1.0',
                display_name='Bug',
                description='Bug',
                input=dict,
                output=dict)
class SubModelBug(Model):
    def run(self, input: dict) -> dict:
        model_slug = 'token.price-ext'
        model_input = Token(address='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2')

        if input['two']:
            res = self.context.run_model(model_slug, input=model_input, block_number=14187946)
            print(self.context.block_number, res)
            # res = self.context.run_model(model_slug, input=model_input, block_number=14194417)
            # print(res)
        else:
            res = self.context.run_model(model_slug, input=model_input, block_number=14194417)
            print(self.context.block_number, res)

        return {}


@Model.describe(slug='finance.run-model-bug',
                version='1.0',
                display_name='Bug',
                description='Bug',
                input=dict,
                output=dict)
class RunModelBug(Model):
    def run(self, input: dict) -> dict:
        model_slug = 'token.price-ext'
        model_input = Token(address='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2')

        res = self.context.run_model(model_slug, input=model_input, block_number=14187946)
        print(self.context.block_number, res)
        res = self.context.run_model(model_slug, input=model_input, block_number=14194417)
        print(self.context.block_number, res)

        self.context.run_model('finance.sub-model-bug', input={'two': False})
        self.context.run_model('finance.sub-model-bug', input={'two': True})

        return {}
