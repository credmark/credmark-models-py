from credmark.cmf.model import Model
from credmark.dto import EmptyInput


@Model.describe(
    slug='contrib.neilz',
    display_name='An example of a contrib model',
    description="This model exists simply as an example of how and where to \
        contribute a model to the Credmark framework",
    version='1.0',
    developer='neilz.eth',
    category='example',
    output=dict
)
class MyModel(Model):
    def run(self, _: EmptyInput):
        return {
            "credmarkFounder": "Neil",
            "message": "You are a modeler. Thank you modeler."
        }
