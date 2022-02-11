from credmark.model import Model, manifest_v1


@manifest_v1(slug='var',
             version='1.0',
             display_name='Value at Risk',
             description='Value at Risk')
class Var(Model):
    def run(self, input) -> dict:
        """
            Var takes in a portfolio object,
            a list of prices per token into the past,
            a price window,
            and a worst case percentage.

            It calculates the usd value of the portfolio for each of the blockstamps/timestamps.
            It then calculates the change in value over the window period for each timestamp,
            it returns the one that hits the input percentage.

        """
        result = {'value': 'not yet implemented'}
