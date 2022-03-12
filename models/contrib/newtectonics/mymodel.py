import credmark.model
import credmark.types


@credmark.model.describe(
    slug='contrib.neilz',
    version='1.0',
    developer='neilz.eth',
    input=None,
    output=dict
)
class MyModel(credmark.model.Model):
    def run(self, input):
        return {
            "credmarkFounder": "Neil",
            "message": "You are a modeler. Thank you modeler."
        }
