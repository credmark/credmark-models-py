# pylint: disable=unused-import

from credmark.cmf.ipython import create_cmf
from credmark.cmf.types import Records, Token


def main():
    cmf_param = {
        'block_number': None,
    }

    context, _model_loader = create_cmf(cmf_param)

    print(context.block_number)

    crv_token = Token('0xD533a949740bb3306d119CC777fa900bA034cd52')
    print(crv_token.symbol, crv_token.decimals,
          crv_token.functions.rate().call())

    result = context.run_model(
        'price.cex', {'base': crv_token})  # type: ignore
    print(result)
    print(result['price'])  # type: ignore

    df = context.run_model(
        'uniswap-v2.lp-fee-history',
        {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
         "lp": "0x76E2E2D4d655b83545D4c50D9521F5bc63bC5329"},  # type: ignore
        return_type=Records).to_dataframe()  # type: ignore
    print(df)


if __name__ == '__main__':
    main()
