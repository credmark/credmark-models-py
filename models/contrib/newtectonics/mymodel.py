import credmark.model


@credmark.model.describe(slug='neils-model', version='1.0')
class MyModel(credmark.model.Model):
    def run(self, input):
        return {
            "founder": "Neil",
            "message": "You are a modeler. Thank you modeler."
        }
