from credmark.model import Model


class SphereVolume(Model):

    def run(self, input):

        result = {'value': 'ERROR, see logs.'}

        try:
            r = input['radius']
            pi = self.context.run_model('pi')['value']
            volume = 4/3 * pi * pow(r, 3)
            result = {'value': volume}
        except KeyError as err:
            self.logger.error('Required input parameter %s missing.' % err)

        return result
