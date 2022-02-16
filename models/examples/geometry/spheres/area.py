import credmark.model
from credmark.model import ModelRunError


@credmark.model(slug='geometry-spheres-area',
                version='1.0',
                display_name='Sphere Surface Area',
                description='Compute the surface area of a sphere given its radius')
class SphereArea:
    context: credmark.model.ModelContext

    def run(self, input) -> dict:

        try:
            r = input['radius']
            pi = self.context.run_model('pi')['value']
            area = 4 * pi * pow(r, 2)
            result = {'value': area}
        except KeyError as err:
            raise ModelRunError('Required input parameter %s missing.' % err)

        return result
