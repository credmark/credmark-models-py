from credmark.model import Model, manifest_v1


@manifest_v1(slug='historical-pi',
             version='1.0',
             display_name='Historical Pi',
             description='The value of Pi at different points in History')
class HistoricalPi(Model):

    """
    This example runs the pi model over blocks 14000000 - block 14100000 using
    the series.blockStartEndInterval model. 
    """

    def run(self, input) -> dict:

        res = self.context.run_model('series.blockStartEndInterval', {
                                     "modelSlug": "pi",
                                     "start": "14000000",
                                     "end": "14100000",
                                     "interval": "10000",
                                     "modelInput": {}})
        return res


@manifest_v1(slug='historical-staked-xcmk',
             version='1.0',
             display_name='Historical Staked xCMK')
class HistoricalXCmkStaked(Model):

    """
    This example runs the pi model over blocks 14000000 - block 14100000 using
    the series.blockStartEndInterval model. 
    """

    def run(self, input) -> dict:

        res = self.context.run_model('series.blockStartEndInterval', {
                                     "modelSlug": "xcmk-cmk-staked",
                                     "start": "13804835",
                                     "end": str(self.context.block_number),
                                     "interval": "10000",
                                     "modelInput": {}})
        return res
