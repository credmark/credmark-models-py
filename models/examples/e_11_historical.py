from datetime import datetime
from credmark.cmf.model import Model
from credmark.dto import EmptyInput
from models.dtos.example import ExampleHistoricalOutput


@Model.describe(
    slug='example.historical',
    version='1.2',
    display_name='Example - Historical',
    description='This model demonstrates how to run a model over a period of time',
    developer='Credmark',
    input=EmptyInput,
    output=ExampleHistoricalOutput)
class ExampleHistorical(Model):
    def run(self, _) -> ExampleHistoricalOutput:
        output = ExampleHistoricalOutput(
            title="11a. Example - Historical",
            description="This model demonstrates how to run a model over a period of time",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_11_historical.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "reference/credmark.cmf.model.utils.historical_util.HistoricalUtil.html"
            "#credmark.cmf.model.utils.historical_util.HistoricalUtil.run_model_historical",
            model_slug="example.model",
        )

        output.log("You can use the run_model_historical method of the historical util in "
                   "context to run model over an interval over a fixed window.")
        output.log("You can move the window by providing end_timestamp. Window can also be "
                   "snapped by duration.")

        output.log_io(input="model_historical_output = "
                      "self.context.historical.run_model_historical(\n"
                      "\t'example.model\n',"
                      "\twindow='5 days\n',"
                      "\tinterval='1 day\n',"
                      "\tsnap_clock='1 day')",
                      output="")
        output.log("----------------------------------------"
                   "----------------------------------------")
        model_historical_output = self.context.historical.run_model_historical(
            'example.model',
            window='5 days',
            interval='1 day',
            snap_clock='1 day')
        output.log("----------------------------------------"
                   "----------------------------------------")
        output.log_io(input="", output=model_historical_output)

        output.log("You can get historical elements by index, blocknumber as well as time")
        output.log_io(input="model_historical_output[2]",
                      output=model_historical_output[2])

        output.log(f"To get model result at block number {model_historical_output[1].blockNumber}")
        output.log_io(input=f"model_historical_output.get("
                      f"block_number={model_historical_output[1].blockNumber})",
                      output=model_historical_output.get(
                          block_number=model_historical_output[1].blockNumber))

        output.log("To get model result nearest to the block one hour from now:")
        output.log_io(input="model_historical_output.get("
                      "timestamp=int(datetime.now().timestamp()) - 3600)",
                      output=model_historical_output.get(
                          timestamp=int(datetime.now().timestamp()) - 3600))

        output.log("You can also iterate over historical output. To map result to a "
                   "list of block numbers: ")
        output.log_io(input="list(map(lambda x: x.blockNumber, model_historical_output))",
                      output=list(map(lambda x: x.blockNumber, model_historical_output)))
        output.model_historical_output = model_historical_output
        return output


@Model.describe(
    slug='example.historical-block',
    version='1.2',
    display_name='Example - Historical Block',
    description='This model demonstrates how to run a model over a series of historical blocks',
    developer='Credmark',
    input=EmptyInput,
    output=ExampleHistoricalOutput)
class ExampleHistoricalBlock(Model):
    def run(self, _) -> ExampleHistoricalOutput:
        output = ExampleHistoricalOutput(
            title="11b. Example - Historical Block",
            description="This model demonstrates how to run a model over a series "
            "of historical blocks",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_11_historical.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "reference/credmark.cmf.model.utils.historical_util.HistoricalUtil.html"
            "#credmark.cmf.model.utils.historical_util.HistoricalUtil"
            ".run_model_historical_blocks",
            model_slug="example.model",
        )

        output.log("You can use the run_model_historical_blocks method of the historical util in "
                   "context to run model over an interval over a fixed window of blocks.")
        output.log("You can move the window by providing end_block. Window can also be "
                   "snapped by duration.")

        output.log_io(input="model_historical_output = "
                      "self.context.historical.run_model_historical_blocks(\n"
                      "\t'example.model',\n"
                      "\twindow=1000,\n"
                      "\tinterval=200,\n"
                      "\tsnap_clock=500)",
                      output="")
        output.log("----------------------------------------"
                   "----------------------------------------")
        model_historical_output = self.context.historical.run_model_historical_blocks(
            'example.model',
            window=1000,
            interval=200,
            snap_block=500,
            model_return_type=dict)
        output.log("----------------------------------------"
                   "----------------------------------------")
        output.log_io(input="", output=model_historical_output)

        output.log("You can get historical elements by index, blocknumber as well as time")
        output.log_io(input="model_historical_output[2]",
                      output=model_historical_output[2])

        output.log(f"To get model result at block number {model_historical_output[1].blockNumber}")
        output.log_io(input=f"model_historical_output.get("
                      f"block_number={model_historical_output[1].blockNumber})",
                      output=model_historical_output.get(
                          block_number=model_historical_output[1].blockNumber))

        output.log("To get model result nearest to the block one hour from now:")
        output.log_io(input="model_historical_output.get("
                      "timestamp=int(datetime.now().timestamp()) - 3600)",
                      output=model_historical_output.get(
                          timestamp=int(datetime.now().timestamp()) - 3600))

        output.log("You can also iterate over historical output. To map result to a list "
                   "of block number and echo message: ")
        output.log_io(input="list(map(lambda x: x.blockNumber, model_historical_output))",
                      output=list(map(lambda x: {"block_number": x.blockNumber,
                                                 "echo": x.output["echo"]},
                                      model_historical_output)))
        output.model_historical_output = model_historical_output
        return output
