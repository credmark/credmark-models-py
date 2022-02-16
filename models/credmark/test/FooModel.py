import credmark.model


@credmark.model(slug='Foo',
                version='1.0',
                display_name='FooModel',
                description='FooModel')
class FooModel:
    context: credmark.model.ModelContext

    def run(self, input) -> dict:
        print(self._manifest)
        return {'value': 42}
