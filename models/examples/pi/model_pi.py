from credmark.model import Model, manifest_v1


@manifest_v1(slug='pi',
             version='1.0',
             display_name='PI',
             description='PI')
class PIModel(Model):

    def run(self, input) -> dict:
        return {'value': 3.1415}
