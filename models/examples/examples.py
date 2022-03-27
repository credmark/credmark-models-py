import credmark.model

@credmark.model.describe(
    slug='example.all',
    version='1.0',
    display_name='All Usage Examples',
    description='This model runs all of the Credmark Example Models',
    developer='Credmark',
    output=dict)
class AllExample(credmark.model.Model):
    def run(self, input) -> dict:
        
        """
            This model runs all of the Credmark Example Models
        """
        self.logger.info(f"This model runs all of the example Credmark Models demonstrating the functionality of the credmark model framework")
        self.logger.info(f"---------------------")
        self.logger.info(f"------ Address ------")
        self.logger.info(f"---------------------")
        self.context.models.example.address()
        self.logger.info(f"---------------------")
        self.logger.info(f"---- BlockNumber ----")
        self.logger.info(f"---------------------")
        self.context.models.example.block_number()
        self.logger.info(f"---------------------")
        self.logger.info(f"------ Account ------")
        self.logger.info(f"---------------------")
        self.context.models.example.account()
        self.logger.info(f"---------------------")
        self.logger.info(f"------ Contract -----")
        self.logger.info(f"---------------------")
        self.context.models.example.contract()
        return {"message": "see https://github.com/credmark/credmark-models-py/blob/main/models/examples/address_examples.py for examples of Address usage"}
