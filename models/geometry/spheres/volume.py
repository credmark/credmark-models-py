from credmark import Model

class SphereVolume(Model):

    def run(self, data):

        RADIUS = 'radius'

        result = {'value': 'ERROR, see logs.'}
        
        try:
            r = data[RADIUS]
            pi = self.context.run_model('pi')['value']
            volume = 4/3 * pi * pow(r, 3)
            result = {'value': volume}
        except KeyError:
            self.logger.error('Required input parameter %s missing.' % RADIUS)

        return result
