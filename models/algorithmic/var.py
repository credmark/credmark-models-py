from credmark import Model

class Var(Model):
    def run(self, data):
        """

            Var takes in a portfolio object,
            a list of prices per token into the past,
            a price window,
            and a worst case percentage.

            It calculates the usd value of the portfolio for each of the blockstamps/timestamps.
            It then calculates the change in value over the window period for each timestamp,
            it returns the one that hits the input percentage.

        """
        result = {'value': 'not implemented'}