from credmark.model import Model

class FooModel(Model):
   def run(self, data):
      return {'value': 42}