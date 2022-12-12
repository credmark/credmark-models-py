# pylint: disable=unused-import

from credmark.cmf.ipython import create_cmf
from credmark.cmf.types import Token, Contract, Address, Account, BlockNumber


def main():
    cmf_param = {
        'block_number': None,
    }

    context, _model_loader = create_cmf(cmf_param)

    print(context.block_number)

    crv_token = Token('0xD533a949740bb3306d119CC777fa900bA034cd52')
    print(crv_token.symbol, crv_token.decimals)

    context.run_model('price.cex', {'base': crv_token})  # type: ignore


if __name__ == '__main__':
    main()
