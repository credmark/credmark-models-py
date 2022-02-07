from credmark import Model


class RunnerTestModel(Model):
    """A test model that runs another model that's specified
    in the input. For example: {"model":"pi"}
    """

    def run(self, data):

        model = data.get('model')

        if model:
            res = self.context.run_model(model, None)
        else:
            res = 'No model specified'

        return {'model': model, 'result': res}
