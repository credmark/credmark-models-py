from credmark.model import Model, manifest_v1


class FooModel(Model):
    def run(self, input) -> dict:
        print(self.slug, self.version, self.display_name, self.description)
        return {'value': 42}
