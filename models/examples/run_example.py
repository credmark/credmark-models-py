import credmark.model


@credmark.model.describe(slug='example.run-test',
                         version='1.0',
                         display_name='Runner test model',
                         description='Test model runs another model specified with \'model\' in input.',
                         developer='Credmark')
class RunnerTestModel(credmark.model.Model):
    """A test model that runs another model that's specified
    in the input. For example: {"model":"example.echo"}
    """

    def run(self, input: dict) -> dict:

        model = input.get('model')

        if model:
            res = self.context.run_model(model, input.get('input'))
        else:
            res = 'No model specified'

        return {'model': model, 'output': res}
