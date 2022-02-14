import credmark.model
from credmark.model import ModelRunError


@credmark.model(slug='geometry-spheres-volume',
                version='1.0',
                display_name='Sphere Volume',
                description='Compute the volume of a sphere given its radius')
class SphereVolume:

    def run(self, input) -> dict:

        try:
            r = input['radius']
            pi = self.context.run_model('pi')['value']
            volume = 4/3 * pi * pow(r, 3)
            result = {'value': volume}
        except KeyError as err:
            raise ModelRunError('Required input parameter %s missing.' % err)

        return result
