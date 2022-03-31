from credmark.cmf.model import Model


@Model.describe(
    slug='example.all',
    version='1.0',
    display_name='All Usage Examples',
    description='This model runs all of the Credmark Example Models',
    developer='Credmark',
    output=dict)
class AllExample(Model):
    def run(self, input) -> dict:
        """
            This model runs all of the Credmark Example Models
        """

        self.logger.info("This model runs all of the example Credmark Models "
                         "demonstrating the functionality of the credmark model framework")
        self.logger.info("---------------------")
        self.logger.info("------ Address ------")
        self.logger.info("---------------------")
        self.context.models.example.address()
        self.logger.info("---------------------")
        self.logger.info("---- BlockNumber ----")
        self.logger.info("---------------------")
        self.context.models.example.block_number()
        self.logger.info("---------------------")
        self.logger.info("------ Account ------")
        self.logger.info("---------------------")
        self.context.models.example.account()
        self.logger.info("---------------------")
        self.logger.info("------ Contract -----")
        self.logger.info("---------------------")
        self.context.models.example.contract()
        return {"message": "see https://github.com/credmark/credmark-models-py/blob/main/models/examples/address_examples.py for examples of Address usage"}  # pylint: disable=line-too-long
