from credmark.model import Model, manifest_v1
from credmark.model.errors import ModelRunError


@manifest_v1(slug='geometry-spheres-area',
             version='1.0',
             display_name='Sphere Surface Area',
             description='Compute the surface area of a sphere given its radius')
class SphereArea(Model):

    def run(self, input) -> dict:

        try:
            r = input['radius']
            pi = self.context.run_model('pi')['value']
            area = 4 * pi * pow(r, 2)
            result = {'value': area}
        except KeyError as err:
            raise ModelRunError('Required input parameter %s missing.' % err)

        return result
