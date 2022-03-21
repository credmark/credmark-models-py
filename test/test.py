if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.join('..', 'credmark-model-framework-py'))

    import credmark.model

    @credmark.model.describe(slug='Foo',
                             version='1.0',
                             display_name='FooModel',
                             description='FooModel')
    class FooModel(credmark.model.Model):
        context: credmark.model.ModelContext

        def run(self, input) -> dict:
            self.logger.info(self._manifest)
            return {'value': 42}

    import credmark.credmark_dev
    credmark.credmark_dev.main()
