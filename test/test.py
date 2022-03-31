if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.join('..', 'credmark-model-framework-py'))

    from credmark.cmf.model import Model, ModelContext

    @Model.describe(slug='Foo',
                    version='1.0',
                    display_name='FooModel',
                    description='FooModel')
    class FooModel(Model):
        context: ModelContext

        def run(self, input) -> dict:
            self.logger.info(self._manifest)
            return {'value': 42}

    import credmark.cmf.credmark_dev
    credmark.cmf.credmark_dev.main()
