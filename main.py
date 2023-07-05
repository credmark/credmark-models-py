import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Response
from typing import Union

import credmark.cmf
# from credmark.cmf.engine.cache import ModelRunCache
from credmark.cmf.engine.context import EngineModelContext
from credmark.cmf.engine.model_loader import ModelLoader
from credmark.cmf.engine.web3_registry import Web3Registry
from credmark.dto import DTO
from credmark.dto.encoder import json_dumps

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level='INFO',
    filename=None,
    filemode='w')

model_loader = ModelLoader(['models'], 'models.json')
model_loader.log_errors()

# model_cache = ModelRunCache("models-cache.db")

app = FastAPI()

env_chain_to_provider_url = Web3Registry.load_providers_from_env()


class BlockSample(DTO):
    number: int
    timestamp: int
    sampleTimestamp: int


class ModelRunBody(DTO):
    chainId: int = 1
    blockNumber: Union[BlockSample, int, None] = None
    slug: str
    version: Union[str, None] = None
    input: dict = {}
    fromBlock: Union[BlockSample, int, None] = None
    runId: Union[str, None] = None
    depth: int = 0
    apiUrl: str
    providerUrlMap: Union[dict, None] = None


# @app.on_event("shutdown")
# def shutdown_event():
#     model_cache.close()


@app.get("/")
def root():
    return 'OK'


@app.get("/list")
def list_models():
    return {
        'cmfVersion': credmark.cmf.__version__,
        'models': model_loader.loaded_model_manifests(),
    }


@app.post("/run")
def run_model(body: ModelRunBody):
    chain_to_provider_url = body.providerUrlMap \
        if body.providerUrlMap is not None \
        else env_chain_to_provider_url
    block = body.blockNumber.dict() \
        if isinstance(body.blockNumber, BlockSample) \
        else body.blockNumber
    from_block = body.fromBlock.dict() \
        if isinstance(body.fromBlock, BlockSample) \
        else body.fromBlock

    result = EngineModelContext.create_context_and_run_model(
        chain_id=body.chainId,
        block=block,
        model_slug=body.slug,
        model_version=body.version,
        input=body.input,
        from_block=from_block,
        model_loader=model_loader,
        chain_to_provider_url=chain_to_provider_url,
        api_url=body.apiUrl,
        run_id=body.runId,
        depth=body.depth,
        model_cache=False)

    return Response(content=json_dumps(result), media_type="application/json")
