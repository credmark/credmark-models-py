from credmark.model import Model, manifest_v1


@manifest_v1(slug='pi',
             version='2.0',
             display_name='PI',
             description='PI')
class PIModel2(Model):

    def run(self, input) -> dict:
        ret = self.context.run_model('pi', input, version='1.0')
        if ret:
            ret['v2'] = True
        return ret
