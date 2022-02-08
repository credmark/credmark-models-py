from credmark.model import Model


class SphereArea(Model):

    def run(self, input):

        result = {'value': 'ERROR, see logs.'}

        try:
            r = input['radius']
            pi = self.context.run_model('pi')['value']
            area = 4 * pi * pow(r, 2)
            result = {'value': area}
        except KeyError as err:
            self.logger.error('Required input parameter %s missing.' % err)

        return result
