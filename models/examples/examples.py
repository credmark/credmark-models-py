from credmark.cmf.model import Model
from models.dtos.example import ExampleAllModelsOutput


@Model.describe(
    slug='example.all',
    version='1.2',
    display_name='Example - All',
    description='This model runs all of the Credmark Example Models',
    developer='Credmark',
    output=ExampleAllModelsOutput)
class AllExample(Model):
    def run(self, _) -> ExampleAllModelsOutput:

        output = ExampleAllModelsOutput(
            title="Example - All",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/examples.py",
            model_outputs=[]
        )

        output.log("This model runs all of the example Credmark Models "
                   "demonstrating the functionality of the credmark model framework")

        example_models = [
            'example.model',
            'example.dto',
            'example.dto-type-test-1',
            # 'example.dto-type-test-2',
            'example.address',
            'example.account',
            'example.contract',
            'example.token',
            'example.ledger-blocks',
            'example.ledger-transactions',
            'example.ledger-aggregates',
            'example.ledger-receipts',
            # 'example.ledger-token-transfers',
            'example.ledger-tokens',
            'example.ledger-logs',
            'example.ledger-contracts',
            'example.ledger-traces',
            'example.block-number',
            'example.block-time',
            'example.model-run',
            'example.historical',
            'example.historical-block',
            'example.iteration',
            # 'example.data-error-1',
            # 'example.data-error-2',
            'example.libraries',
        ]

        model_outputs = []
        for model_slug in example_models:
            output.log(f"Running {model_slug}")
            output.log("----------------------------------------"
                       "----------------------------------------")
            model_output = self.context.run_model(model_slug)
            output.log("----------------------------------------"
                       "----------------------------------------")
            model_outputs.append({
                "model_slug": model_slug,
                "model_output": model_output
            })

        output.model_outputs = model_outputs

        return output
