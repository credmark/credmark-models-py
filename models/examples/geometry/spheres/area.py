from credmark.model import Model
from credmark.model.errors import ModelRunError


class SphereArea(Model):

    def run(self, input):

        try:
            r = input['radius']
            pi = self.context.run_model('pi')['value']
            area = 4 * pi * pow(r, 2)
            result = {'value': area}
        except KeyError as err:
            raise ModelRunError('Required input parameter %s missing.' % err)

        return result
