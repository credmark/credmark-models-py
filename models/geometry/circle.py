from credmark import Model

class Circle(Model):
    """
    This is the base class for all circle models. It's assumed that
    radius is the only needed input for all circle-related
    computation.
    """

    def get_result(self, radius):
        pass

    def run(self, data):

        RADIUS = 'radius'

        result = {'value': 'ERROR, see logs.'}
        
        try:
            result = {'value': self.get_result(data[RADIUS])}
        except KeyError:
            self.logger.error('Required input parameter %s missing.' % RADIUS)

        return result

