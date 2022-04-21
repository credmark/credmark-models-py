



from typing import List, Union
from credmark.cmf.model import Model, describe
from credmark.cmf.model.errors import ModelRunError
from credmark.dto import DTO, IterableListGenericDTO

class ModelComposeEachDTO(DTO):
    model_slug:str
    model_input_slug: str
    model_input_input: DTO

class ModelComposeEachOutputRowDTO(DTO):
    input:Union[dict,DTO]
    output:Union[dict,DTO]
    
class ModelComposeEachOutputDTO(IterableListGenericDTO):
    _iterator:str = "results"
    results: List[ModelComposeEachOutputRowDTO]

@describe(
    slug="compose.each",
    version="1.0",
    input=ModelComposeEachDTO,
    output=ModelComposeEachOutputDTO)
class ComposeEach(Model):
    def run(self, input: ModelComposeEachDTO) -> ModelComposeEachOutputDTO:
        list_model = self.context.run_model(
            slug=input.model_input_slug,
            input=input.model_input_input,
            return_type=dict)
        for key in list_model.keys():
            if isinstance(list_model[key], List):
                results = []
                for row in list_model[key]:
                    row_result = self.context.run_model(slug=input.model_slug, input=row)
                    results.append(ModelComposeEachOutputRowDTO(input=row, output=row_result))
                return ModelComposeEachOutputDTO(results=results)
        raise ModelRunError("Not an iterable Input")