from credmark.model import Model, manifest_v1


@manifest_v1(slug='Foo',
             version='1.0',
             display_name='FooModel',
             description='FooModel')
class FooModel(Model):
    def run(self, input) -> dict:
        print(self._manifest['model'])
        return {'value': 42}
