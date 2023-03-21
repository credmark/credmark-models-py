# pylint:disable=line-too-long, invalid-name

import pandas as pd

from credmark.cmf.ipython import create_cmf

if __name__ == '__main__':
    local_cmf_param = {
        'block_number': None,
        'chain_to_provider_url': {'1': 'http://192.168.68.122:8545'},
        'api_url': 'http://192.168.68.122:8700',
        'use_local_models': '-',  # use local to speed up
    }
    local_context, _model_loader = create_cmf(local_cmf_param)

    prod_cmf_param = {
        'block_number': None,
        'chain_to_provider_url': {'1': 'http://192.168.68.122:8545'},
        'api_url': 'https://gateway.credmark.com',
        'use_local_models': '-',
    }
    prod_context, _model_loader = create_cmf(prod_cmf_param)

    blocks = [16_802_605, 16_804_605, 16_811_605, 16_862_071, 16_402_605]
    csv_str_list = []
    for block in blocks:
        df_result = pd.DataFrame(
            {'Token': ['USDC', 'DAI', 'USDT', 'WETH', 'AAVE'],
             'Current': 0,
             'Updated': 0,
             'Oracle': 0,
             'Current Diff (%)': 0,
             'Updated Diff (%)': 0}
        )
        for row_n, row in df_result.iterrows():
            symbol = row['Token']
            current = prod_context.run_model(
                'price.dex-blended', input={'symbol': symbol}, return_type=dict, block_number=block)['price']  # type: ignore

            updated = local_context.run_model(
                'price.dex-blended', input={'symbol': symbol}, block_number=block)['price']  # type: ignore

            oracle = prod_context.run_model('price.oracle-chainlink',
                                            input={'base': symbol}, block_number=block)['price']  # type: ignore

            df_result.loc[row_n, 'Current'] = current  # type: ignore
            df_result.loc[row_n, 'Updated'] = updated  # type: ignore
            df_result.loc[row_n, 'Oracle'] = oracle  # type: ignore
            df_result.loc[row_n, 'Current Diff (%)'] = (current - oracle) / oracle  # type: ignore
            df_result.loc[row_n, 'Updated Diff (%)'] = (updated - oracle) / oracle  # type: ignore

        df_result.reset_index(drop=False, inplace=True)
        df_result.columns = [block, 'Token', 'Current', 'Updated', 'Oracle', 'Current Diff (%)', 'Updated Diff (%)']
        csv_str_list.append(df_result.to_csv(index=False))
        print(f'Finished {block}')

    f_out = 'tmp/price_test_v2.csv'
    with open(f_out, 'w') as f:
        for l in csv_str_list:
            f.write(l)
            f.write('\n')
    print(f'Wrote to {f_out}')
