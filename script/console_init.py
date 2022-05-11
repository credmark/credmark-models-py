import importlib


def load_modules(environ):
    environ['abi_lookup'] = importlib.import_module('models.tmp_abi_lookup')

    aave_v2 = importlib.import_module('models.credmark.protocols.lending.aave.aave_v2')
    environ['AaveDebtInfo'] = aave_v2.AaveDebtInfo
    environ['AaveDebtInfos'] = aave_v2.AaveDebtInfos

    compound_v2 = importlib.import_module('models.credmark.protocols.lending.compound.compound_v2')
    environ['CompoundV2PoolInfo'] = compound_v2.CompoundV2PoolInfo
    environ['CompoundV2PoolValue'] = compound_v2.CompoundV2PoolValue

    curve_finance = importlib.import_module('models.credmark.protocols.dexes.curve.curve_finance')
    environ['CurveFiPoolInfo'] = curve_finance.CurveFiPoolInfo
    environ['CurveFiPoolInfos'] = curve_finance.CurveFiPoolInfos

    dto_volume = importlib.import_module('models.dtos.volume')
    environ['TradingVolume'] = dto_volume.TradingVolume
    environ['TokenTradingVolume'] = dto_volume.TokenTradingVolume

    dto_prices = importlib.import_module('models.dtos.price')
    environ['PoolPriceInfo'] = dto_prices.PoolPriceInfo
    environ['PoolPriceInfos'] = dto_prices.PoolPriceInfos
    environ['PoolPriceAggregatorInput'] = dto_prices.PoolPriceAggregatorInput

    print(environ.keys())
