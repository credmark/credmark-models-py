import credmark.model


@credmark.model.it(slug='pi',
                   version='1.0',
                   display_name='PI',
                   description='PI')
class PIModel(credmark.model.Model):

    def run(self, input) -> dict:
        return {'value': 3.1415}
