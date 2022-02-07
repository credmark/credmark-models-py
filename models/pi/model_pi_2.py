from credmark import Model


class PIModel2(Model):

    def run(self, data):
        ret = self.context.run_model('pi', data, version='1.0')
        if ret:
            ret['v2'] = True
        return ret
