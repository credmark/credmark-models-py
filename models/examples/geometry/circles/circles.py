import math

from credmark.model import Model, manifest_v1

from ..circle import Circle


@manifest_v1(slug='geometry-circles-area',
             version='1.0',
             display_name='Circle Area',
             description='Compute the area of a circle given its radius')
class CircleArea(Circle):

    def get_result(self, radius):
        return math.pi * pow(radius, 2)


@manifest_v1(slug='geometry-circles-circumference',
             version='1.0',
             display_name='Circle Circumference',
             description='Compute the circumference of a circle given its radius')
class CircleCircumference(Circle):

    def get_result(self, radius):
        return 2 * math.pi * radius
