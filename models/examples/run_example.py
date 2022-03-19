import credmark.model

from credmark.dto import DTO


class RunTestIn(DTO):
    model: str
    input: dict


class RunTestOut(DTO):
    model: str
    output: dict


@credmark.model.describe(slug='example.run-test',
                         version='1.0',
                         display_name='Runner test model',
                         description='Test model runs another model specified with \'model\' in input.',
                         developer='Credmark',
                         input=RunTestIn,
                         output=RunTestOut)
class RunnerTestModel(credmark.model.Model):
    """A test model that runs another model that's specified
    in the input. For example: {"model":"example.echo"}
    """

    def run(self, input: RunTestIn) -> RunTestOut:

        model = input.model

        if model:
            res = self.context.run_model(model, input.input)
        else:
            res = {'result': 'No model specified'}

        return RunTestOut(model=model, output=res)
