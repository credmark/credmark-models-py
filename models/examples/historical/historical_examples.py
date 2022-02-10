from credmark.model import Model


class HistoricalPi(Model):

    def run(self, input) -> dict:

        res = self.context.run_model('series.blockStartEndInterval', {
                                     "modelSlug": "pi",
                                     "start": "14000000",
                                     "end": "14100000",
                                     "interval": "10000",
                                     "modelInput": {}})
        return res
