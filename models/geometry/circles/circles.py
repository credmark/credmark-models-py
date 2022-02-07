from models.geometry.circle import Circle
import math

class CircleArea(Circle):

    def get_result(self, r):
        return math.pi * pow(r, 2)

class CircleCircumference(Circle):

    def get_result(self, r):
        return 2 * math.pi * r
