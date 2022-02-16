import math

import credmark.model

from ..circle import Circle


@credmark.model(slug='geometry-circles-area',
                version='1.0',
                display_name='Circle Area',
                description='Compute the area of a circle given its radius')
class CircleArea(Circle, list):
    context: credmark.model.ModelContext

    def get_result(self, radius):
        return math.pi * pow(radius, 2)


@credmark.model(slug='geometry-circles-circumference',
                version='1.0',
                display_name='Circle Circumference',
                description='Compute the circumference of a circle given its radius')
class CircleCircumference(Circle):
    context: credmark.model.ModelContext

    def get_result(self, radius):
        return 2 * math.pi * radius
