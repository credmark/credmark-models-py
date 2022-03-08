import credmark.model
import credmark.types


@credmark.model.describe(slug='contrib.neils-model', version='1.0')
class MyModel(credmark.model.Model):
    def run(self, input):
        return {
            "founder": "Neil",
            "message": "You are a modeler. Thank you modeler."
        }
