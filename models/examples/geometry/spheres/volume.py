from credmark.model import Model
from credmark.model.errors import ModelRunError


class SphereVolume(Model):

    def run(self, input):

        try:
            r = input['radius']
            pi = self.context.run_model('pi')['value']
            volume = 4/3 * pi * pow(r, 3)
            result = {'value': volume}
        except KeyError as err:
            raise ModelRunError('Required input parameter %s missing.' % err)

        return result
