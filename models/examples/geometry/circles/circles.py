from ..circle import Circle
import math


class CircleArea(Circle):

    def get_result(self, radius):
        return math.pi * pow(radius, 2)


class CircleCircumference(Circle):

    def get_result(self, radius):
        return 2 * math.pi * radius
