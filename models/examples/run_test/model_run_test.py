from credmark.model import Model


class RunnerTestModel(Model):
    """A test model that runs another model that's specified
    in the input. For example: {"model":"pi"}
    """

    def run(self, input):

        model = input.get('model')

        if model:
            res = self.context.run_model(model, input.get('input'))
        else:
            res = 'No model specified'

        return {'model': model, 'result': res}
