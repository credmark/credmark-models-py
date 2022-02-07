from credmark import Model
import math


class PIModel(Model):

    def run(self, data):
        return {'value': math.pi}
