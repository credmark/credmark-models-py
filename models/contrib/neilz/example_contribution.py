from credmark.cmf.model import Model


@Model.describe(
    slug='contrib.neilz',
    display_name='An example of a contrib model',
    description="This model exists simply as an example of how and where to \
        contribute a model to the Credmark framework",
    version='1.0',
    developer='neilz.eth',
    output=dict
)
class MyModel(Model):
    def run(self, input):
        return {
            "credmarkFounder": "Neil",
            "message": "You are a modeler. Thank you modeler."
        }
