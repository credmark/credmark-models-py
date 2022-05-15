from credmark.cmf.model import Model
from credmark.dto import EmptyInput
from models.dtos.example import ExampleModelOutput


class RunExampleOutput(ExampleModelOutput):
    model_slug: str
    model_output: dict


@Model.describe(
    slug='example.model-run',
    version='1.2',
    display_name='Example - Model Run',
    description='This model demonstrates how to run a "model" within a model',
    developer='Credmark',
    input=EmptyInput,
    output=RunExampleOutput)
class ExampleModelRun(Model):
    def run(self, _) -> RunExampleOutput:
        output = RunExampleOutput(
            title="9. Example - Model Run",
            description="This model demonstrates how to run a \"model\" within a model",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_09_run.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "components.html#context-run-model",
            model_slug="example.model",
            model_output={}
        )

        output.log("Models are exposed on context.models by their slug (with any \"-\" (hyphens) "
                   "in the slug replaced with \"_\" (underscores)) and can be called like a "
                   "function, passing the input as a DTO or dict or as standard keyword args"
                   " (kwargs).")
        output.log_io(input="self.context.models.example.model({"
                      "\"message\": \"Hello from model-run example\"})",
                      output="")
        output.log("Or you can use the run_model method of the context.")
        output.log_io(input="self.context.run_model("
                      "\n\tslug=\"example.model\","
                      "\n\tinput={\"message\": \"Hello from model-run example\"})",
                      output="")
        output.log("----------------------------------------"
                   "----------------------------------------")
        model_output = self.context.run_model(
            slug='example.model',
            input={"message": "Hello from model-run example"})
        output.log("----------------------------------------"
                   "----------------------------------------")
        output.log_io(input="", output=model_output)

        output.model_output = model_output
        return output
