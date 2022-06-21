echo_cmd ""
echo_cmd "Neil's example:"
echo_cmd ""
test_model 0 contrib.neilz '{}'

echo_cmd ""
echo_cmd "Examples"
echo_cmd ""
test_model 0 example.all '{}' example.contract,example.ledger-transactions,example.block-time
test_model 0 example.model '{}'
test_model 0 example.model-run '{}'
test_model 0 example.contract '{}'
test_model 3 example.data-error-1 '{}'
test_model 3 example.data-error-2 '{}'
test_model 0 example.block-time '{}'
test_model 0 example.block-number '{}'
test_model 0 example.address '{}'
test_model 0 example.libraries '{}'
test_model 0 example.token '{}'
test_model 0 example.dto '{}'
test_model 0 example.dto-type-test-1 '{"positions": [{"amount": "4.2", "asset": {"symbol": "USDC"}},{"amount": "4.4", "asset": {"symbol": "USDT"}}]}'
test_model 1 example.dto-type-test-2 '{"positions": [{"amount": "4.2", "asset": {"symbol": "USDC"}},{"amount": "4.4", "asset": {"symbol": "USDT"}}]}'
test_model 0 example.account '{}'
test_model 0 example.ledger-aggregates '{}'

echo_cmd ""
echo_cmd "Run Historical Examples:"
echo_cmd ""
test_model 0 example.historical '{"model_slug":"token.price","model_input":{"symbol": "USDC"}}' token.price
test_model 0 example.historical '{"model_slug":"token.overall-volume","model_input":{"symbol": "USDC"}}' token.overall-volume # series.time-window-interval, series.time-start-end-interval
test_model 0 example.historical-block '{}' example.libraries # series.block-window-interval, series.block-start-end-interval

echo_cmd ""
echo_cmd "Run Ledger Examples:"
echo_cmd ""
test_model 0 example.ledger-token-transfers '{"address":"0x3812D217bB3A0B43aa16985A616A4e0c6A17C65F"}'
test_model 0 example.ledger-transactions '{}'
test_model 0 example.ledger-receipts '{}'
test_model 0 example.ledger-traces '{}'
test_model 0 example.ledger-blocks '{}'
test_model 0 example.ledger-tokens '{}'
test_model 0 example.ledger-contracts '{}'
test_model 0 example.ledger-logs '{}'

echo_cmd ""
echo_cmd "Run Iteration Examples:"
echo_cmd ""
test_model 0 example.iteration '{}'
