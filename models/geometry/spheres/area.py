from credmark import Model

class SphereArea(Model):

    def run(self, data):

        RADIUS = 'radius'

        result = {'value': 'ERROR, see logs.'}
        
        try:
            r = data[RADIUS]
            pi = self.context.run_model('pi')['value']
            area = 4 * pi * pow(r, 2)
            result = {'value': area}
        except KeyError:
            self.logger.error('Required input parameter %s missing.' % RADIUS)

        return result
