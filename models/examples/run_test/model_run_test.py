import credmark.model


@credmark.model(slug='run-test',
                version='1.0',
                display_name='Runner test model',
                description='Test model runs another model specified with \'model\' in input.')
class RunnerTestModel:
    """A test model that runs another model that's specified
    in the input. For example: {"model":"pi"}
    """
    context: credmark.model.ModelContext

    def run(self, input) -> dict:

        model = input.get('model')

        if model:
            res = self.context.run_model(model, input.get('input'))
        else:
            res = 'No model specified'

        return {'model': model, 'result': res}
