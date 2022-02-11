from credmark.model import Model, manifest_v1
from credmark.model.errors import ModelRunError


@manifest_v1(slug='geometry-spheres-volume',
             version='1.0',
             display_name='Sphere Volume',
             description='Compute the volume of a sphere given its radius')
class SphereVolume(Model):

    def run(self, input) -> dict:

        try:
            r = input['radius']
            pi = self.context.run_model('pi')['value']
            volume = 4/3 * pi * pow(r, 3)
            result = {'value': volume}
        except KeyError as err:
            raise ModelRunError('Required input parameter %s missing.' % err)

        return result
