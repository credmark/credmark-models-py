# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestToken(CMFTest):
    def test_volume(self):
        self.run_model("token.overall-volume-block",
                       {"symbol": "USDC", "block_number": -1000})

        self.run_model("token.overall-volume-block",
                       {"symbol": "USDC", "block_number": self.block_number - 1000})

        self.run_model("token.overall-volume-window",
                       {"symbol": "USDC", "window": "24 hours"})
        self.run_model("token.overall-volume-window",
                       {"address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "window": "24 hours"})
        self.run_model("token.overall-volume-window",
                       {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9", "window": "24 hours"})

        self.run_model("token.overall-volume-block",
                       {"symbol": "ETH", "block_number": -100})
        self.run_model("token.overall-volume-block",
                       {"symbol": "AAVE", "block_number": -100})
        self.run_model("token.overall-volume-block",
                       {"address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "block_number": -100})
        self.run_model("token.overall-volume-block",
                       {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9", "block_number": -100})

        self.run_model("token.volume-segment-block",
                       {"address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "block_number": -100, "n": 3})
        self.run_model("token.volume-segment-block",
                       {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9", "block_number": -100, "n": 3})
        self.run_model("token.volume-segment-block",
                       {"symbol": "AAVE", "block_number": -100, "n": 3})

        self.run_model("token.volume-segment-block",
                       {"address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "block_number": -100})
        self.run_model("token.volume-segment-block",
                       {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9", "block_number": -100, "n": 3})
        self.run_model("token.volume-segment-block",
                       {"symbol": "AAVE", "block_number": -100, "n": 3})

        # SELECT s.number AS "s.number",s.timestamp AS "s.timestamp",s.number AS "from_block",s.timestamp AS "from_timestamp",e.number AS "to_block",e.timestamp AS "to_timestamp",SUM(t.value::NUMERIC) AS "sum_value" FROM raw_ethereum.public.blocks s JOIN raw_ethereum.public.blocks e ON e.number = ((s.number + 556) - 1) LEFT OUTER JOIN raw_ethereum.public.token_transfers t ON t.block_number between s.number and e.number and t.token_address = '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9' WHERE  s.number <= 14249443 AND ( s.number >= 14247775 and s.number < 14249443 ) GROUP BY s.number,s.timestamp,e.number,e.timestamp HAVING MOD(e.number - 14247775, 556) = 0 ORDER BY s.number asc LIMIT 5000
        self.run_model("token.volume-segment-window",
                       {"symbol": "AAVE", "window": "2 hours", "n": 3})
        self.run_model("token.volume-segment-window",
                       {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9", "window": "2 hours", "n": 3})

    def test_netflow(self):
        self.run_model("token.netflow-block",
                       {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9", "block_number": -1000, "netflow_address": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43"})
        self.run_model("token.netflow-window",
                       {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9",
                        "window": "1 day", "netflow_address": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43"})
        self.run_model("token.netflow-segment-block",
                       {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9",
                        "block_number": -1000, "netflow_address": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43", "n": 4})
        self.run_model("token.netflow-segment-window",
                       {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9",
                        "window": "1 day", "netflow_address": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43", "n": 4})

    # Till Transaction table can be fixed
    def no_test_eth_volume(self):
        _query = """
        SELECT s.number AS "s.number",s.timestamp AS "s.timestamp",s.number AS "from_block",s.timestamp AS "from_timestamp",e.number AS "to_block",e.timestamp AS "to_timestamp",SUM(t.value::NUMERIC) AS "sum_value" FROM raw_ethereum.public.blocks s JOIN raw_ethereum.public.blocks e ON e.number = ((s.number + 556) - 1) LEFT OUTER JOIN raw_ethereum.public.transactions t ON t.block_number between s.number and e.number WHERE  s.number <= 14249443 AND ( s.number >= 14248331 and s.number < 14249443 ) GROUP BY s.number,s.timestamp,e.number,e.timestamp HAVING MOD(e.number - 14248331, 556) = 0 ORDER BY s.number asc LIMIT 5000;
        """
        self.run_model("token.volume-segment-window",
                       {"address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "window": "2 hours"})

        _query = """
        SELECT s.number AS "s.number",s.timestamp AS "s.timestamp",s.number AS "from_block",s.timestamp AS "from_timestamp",e.number AS "to_block",e.timestamp AS "to_timestamp",SUM(t.value::NUMERIC) AS "sum_value" FROM raw_ethereum.public.blocks s JOIN raw_ethereum.public.blocks e ON e.number = ((s.number + 556) - 1) LEFT OUTER JOIN raw_ethereum.public.transactions t ON t.block_number between s.number and e.number WHERE  s.number <= 14249443 AND ( s.number >= 14247775 and s.number < 14249443 ) GROUP BY s.number,s.timestamp,e.number,e.timestamp HAVING MOD(e.number - 14247775, 556) = 0 ORDER BY s.number asc LIMIT 5000;
        """
        self.run_model("token.volume-segment-window",
                       {"address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "window": "2 hours", "n": 3})

        self.run_model("token.volume-segment-window",
                       {"address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "window": "2 hours", "n": 2})

    def no_test_eth_flow(self):
        self.run_model("token.netflow-window",
                       {"address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                        "window": "1 day", "netflow_address": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43"})

        self.run_model("token.netflow-block",
                       {"address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                        "block_number": -1000, "netflow_address": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43"})

        _query = """
        SELECT s.number AS "s.number",s.timestamp AS "s.timestamp",s.number AS "from_block",s.timestamp AS "from_timestamp",e.number AS "to_block",e.timestamp AS "to_timestamp",SUM(CASE WHEN t.to_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43' THEN t.value ELSE 0::INTEGER END) AS "inflow",SUM(CASE WHEN t.from_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43' THEN t.value ELSE 0::INTEGER END) AS "outflow",SUM(CASE WHEN t.to_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43' THEN t.value ELSE -t.value END) AS "netflow" FROM raw_ethereum.public.blocks s JOIN raw_ethereum.public.blocks e ON e.number = ((s.number + 6516) - 1) LEFT OUTER JOIN raw_ethereum.public.transactions t ON t.block_number between s.number and e.number and (t.to_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43' or t.from_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43') WHERE  s.number <= 14249443 AND ( s.number > 14223379 and s.number <= 14249443 ) GROUP BY s.number,s.timestamp,e.number,e.timestamp HAVING s.number >= 14223379 and s.number < 14249443 and MOD(e.number - 14223379, 6516) = 0 ORDER BY s.number asc LIMIT 5000
        """
        self.run_model("token.netflow-segment-window",
                       {"address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                        "window": "1 day", "netflow_address": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43", "n": 4})

        _query = """
        SELECT s.number AS "s.number",s.timestamp AS "s.timestamp",s.number AS "from_block",s.timestamp AS "from_timestamp",e.number AS "to_block",e.timestamp AS "to_timestamp",SUM(CASE WHEN t.to_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43' THEN t.value ELSE 0::INTEGER END) AS "inflow",SUM(CASE WHEN t.from_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43' THEN t.value ELSE 0::INTEGER END) AS "outflow",SUM(CASE WHEN t.to_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43' THEN t.value ELSE -t.value END) AS "netflow" FROM raw_ethereum.public.blocks s JOIN raw_ethereum.public.blocks e ON e.number = ((s.number + 1000) - 1) LEFT OUTER JOIN raw_ethereum.public.transactions t ON t.block_number between s.number and e.number and (t.to_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43' or t.from_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43') WHERE  s.number <= 14249443 AND ( s.number > 14245443 and s.number <= 14249443 ) GROUP BY s.number,s.timestamp,e.number,e.timestamp HAVING s.number >= 14245443 and s.number < 14249443 and MOD(e.number - 14245443, 1000) = 0 ORDER BY s.number asc LIMIT 5000
        """
        self.run_model("token.netflow-segment-block",
                       {"address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                        "block_number": -1000, "netflow_address": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43", "n": 4})

    def test_holders(self):
        self.run_model("token.holders",
                       {"address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "top_n": 20})

        self.run_model("token.holders",
                       {"address": "0xFFC97d72E13E01096502Cb8Eb52dEe56f74DAD7B", "top_n": 20})

        # cbETH's first transfer is at block 14160141, created at 14133762
        # query at earlier blocks should return 0
        def _get_first_tx(context, addr):
            with context.ledger.TokenTransfer as tt:
                df = tt.select(tt.columns,
                               where=tt.TOKEN_ADDRESS.eq(addr),
                               order_by=tt.BLOCK_NUMBER.asc(), limit=1)
                return df.iloc[0]['block_number'] if not df.empty else -1
        # _get_first_tx(context, '0xbe9895146f7af43049ca1c1ae358b0541ea49704')
        self.run_model("token.holders-count",
                       {"address": "0xBe9895146f7AF43049ca1c1AE358B0541Ea49704"}, block_number=14130667)

        # USDC first transfer is at block , created at 6082465
        # _get_first_tx(context, '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48')
        self.run_model("token.holders-count",
                       {"address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"}, block_number=6083000)

        self.run_model('token.holders-count',
                       {"address": "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2"})

    def test_transaction(self):
        self.run_model("token.transaction",
                       {"hash": "0x319552805d5f3d0c97e7b6c1e40d0c42817c49406fbff41af0f3ac88b590aa34", "block_number": 15125867}, block_number=15225867)

        self.run_model("token.transaction",
                       {"hash": "0x7ee67c4b2b5540a503fdf3b2f3a44c955c22884c0e286f5d89e67d4d8989264a", "block_number": 13984858}, block_number=15125867)

    def test_account(self):
        self.title("Account Examples")
        self.run_model("account.portfolio", {
                       "address": "0xCE017A1dcE5A15668C4299263019c017154ACE17"})

        # Working but taking long time.
        # Test account 1: 0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0
        # Test account 2: 0xbdfa4f4492dd7b7cf211209c4791af8d52bf5c50
        # self.run_model("account.portfolio", {"address": "0xbdfa4f4492dd7b7cf211209c4791af8d52bf5c50"})

    def test_tokens(self):
        self.title("Token Examples")

        # UniswapV3 pool USDC-WETH 0x7bea39867e4169dbe237d55c8242a8f2fcdcc387
        self.run_model("uniswap-v3.get-pool-info",
                       {"address": "0x7bea39867e4169dbe237d55c8242a8f2fcdcc387"})

        # token.underlying-maybe,price.oracle-chainlink-maybe,price.oracle-chainlink
        # ${token_price_deps}
        self.run_model("price.dex", {"base": {"symbol": "WETH"}})
        # ${token_price_deps}
        self.run_model("price.dex", {"base": {"symbol": "CMK"}})
        # ${token_price_deps}
        self.run_model("price.dex", {"base": {"symbol": "AAVE"}})

        # AAVE: 0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9
        # ${token_price_deps}
        self.run_model("price.dex", {
                       "base": {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9"}})
        # ${token_price_deps}
        self.run_model("price.dex", {"base": {"symbol": "USDC"}})
        # ${token_price_deps}
        self.run_model("price.dex", {"base": {"symbol": "MKR"}})

        # Ampleforth: 0xd46ba6d942050d489dbd938a2c909a5d5039a161
        # ${token_price_deps}
        self.run_model("price.dex", {
                       "base": {"address": "0xd46ba6d942050d489dbd938a2c909a5d5039a161"}})
        # RenFil token: 0xD5147bc8e386d91Cc5DBE72099DAC6C9b99276F5
        # ${token_price_deps}
        self.run_model("price.dex", {
                       "base": {"address": "0xD5147bc8e386d91Cc5DBE72099DAC6C9b99276F5"}})

        # ${token_price_deps}
        self.run_model("price.quote", {
                       "base": {"symbol": "WETH"}, "prefer": "dex"})
        # ${token_price_deps}
        self.run_model("price.quote", {
                       "base": {"symbol": "CMK"}, "prefer": "dex"})
        # ${token_price_deps}
        self.run_model("price.quote", {
                       "base": {"symbol": "AAVE"}, "prefer": "dex"})
        self.run_model("price.quote", {
                       "base": {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9"}, "prefer": "dex"})
        # ${token_price_deps}
        self.run_model("price.quote", {
                       "base": {"symbol": "USDC"}, "prefer": "dex"})
        # ${token_price_deps}
        self.run_model("price.quote", {
                       "base": {"symbol": "MKR"}, "prefer": "dex"})
        self.run_model("price.quote", {
                       "base": {"address": "0xd46ba6d942050d489dbd938a2c909a5d5039a161"}, "prefer": "dex"})
        self.run_model("price.quote", {
                       "base": {"address": "0xD5147bc8e386d91Cc5DBE72099DAC6C9b99276F5"}, "prefer": "dex"})

        # ${token_price_deps}
        self.run_model("price.quote", {
                       "base": {"symbol": "WETH"}, "prefer": "cex"})
        # ${token_price_deps}
        self.run_model("price.quote", {
                       "base": {"symbol": "CMK"}, "prefer": "cex"})
        # ${token_price_deps}
        self.run_model("price.quote", {
                       "base": {"symbol": "AAVE"}, "prefer": "cex"})
        self.run_model("price.quote", {
                       "base": {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9"}, "prefer": "cex"})
        # ${token_price_deps}
        self.run_model("price.quote", {
                       "base": {"symbol": "USDC"}, "prefer": "cex"})
        # ${token_price_deps}
        self.run_model("price.quote", {
                       "base": {"symbol": "MKR"}, "prefer": "cex"})
        self.run_model("price.quote", {
                       "base": {"address": "0xd46ba6d942050d489dbd938a2c909a5d5039a161"}, "prefer": "cex"})
        self.run_model("price.quote", {
                       "base": {"address": "0xD5147bc8e386d91Cc5DBE72099DAC6C9b99276F5"}, "prefer": "cex"})

        self.run_model("token.holders", {"symbol": "CMK"})
        self.run_model("token.swap-pools", {"symbol": "CMK"})

        self.run_model("token.info", {"symbol": "CMK"})
        self.run_model("token.info", {"address": "0x019Ff0619e1D8Cd2d550940eC743fDE6d268AfE2"})
        self.run_model("token.info", {"address": "0x019ff0619e1d8cd2d550940ec743fde6d268afe2"})
        self.run_model("token.info", {"symbol": "MKR"})

        self.run_model('token.total-supply',
                       {"address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"})

        self.run_model('token.balance',
                       {"address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                        "account": "0x55FE002aefF02F77364de339a1292923A15844B8"})

        self.run_model("token.deployment", {
                       "address": "0x019ff0619e1d8cd2d550940ec743fde6d268afe2"})
        self.run_model("token.deployment", {
                       "address": "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2"})  # MKR
        self.run_model("token.deployment", {"symbol": "USDC"})

        # WETH-DAI pool: https://analytics.sushi.com/pairs/0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f
        self.run_model("token.swap-pool-volume",
                       {"address": "0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f"})

        # UniSwap V3 factory: 0x1F98431c8aD98523631AE4a59f267346ea31F984
        self.run_model("token.categorized-supply",
                       {"categories": [
                           {"accounts": {"accounts": [{"address": "0x1F98431c8aD98523631AE4a59f267346ea31F984"}]}, "categoryName": "", "categoryType": "", "circulating": True}],
                           "token": {"symbol": "DAI"}})

        self.run_model('token.all', {'limit': 10})
        self.run_model('token.all', {'limit': 10, 'page': 2})
