import credmark.model


@credmark.model.it(slug='Foo',
                   version='1.0',
                   display_name='FooModel',
                   description='FooModel')
class FooModel(credmark.model.Model):

    def run(self, input) -> dict:
        print(self._manifest)
        return {'value': 42}
