from credmark import Model
import math


class PIModel(Model):

    def run(self, _input):
        return {'value': math.pi}
