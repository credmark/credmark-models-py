from credmark.model import Model


class PIModel2(Model):

    def run(self, input):
        ret = self.context.run_model('pi', input, version='1.0')
        if ret:
            ret['v2'] = True
        return ret
