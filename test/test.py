import credmark.model
import sys
sys.path.insert(0, '..\credmark-model-sdk-py')


@credmark.model.describe(slug='Foo',
                         version='1.0',
                         display_name='FooModel',
                         description='FooModel')
class FooModel(credmark.model.Model):
    context: credmark.model.ModelContext

    def run(self, input) -> dict:
        print(self._manifest)
        return {'value': 42}


if __name__ == '__main__':
    import credmark.credmark_dev
    credmark.credmark_dev.main()
