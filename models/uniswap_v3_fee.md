# Uniswap V3 fee

## Fee

Source:

-   https://github.com/Uniswap/v3-core/blob/main/contracts/UniswapV3Pool.sol#L663

```solidity
function swap(
    address recipient,
    bool zeroForOne,
    int256 amountSpecified,
    uint160 sqrtPriceLimitX96,
    bytes calldata data)
```

1. `amountSpecified` set to be `state.amountSpecifiedRemaining`
2. `state.amountSpecifiedRemaining` sent to `SwapMath.computeSwapStep()` to calculate `feeAmount` and `amountIn`.

```
// https://github.com/Uniswap/v3-core/blob/main/contracts/libraries/SwapMath.sol#L93

    uint256 amountRemainingLessFee = FullMath.mulDiv(uint256(amountRemaining), 1e6 - feePips, 1e6);
    // amountRemaining * (1 - 0.003) / 1 = amountRemaining * 0.997
    // use amountRemaining * 0.997 to calculate amountIn.
    // amountRemaining - amountIn = feeAmount

    // Or
    // amountIn * 0.003 / (1 - 0.0003)
    // In another order of amountIn / (1 - 0.0003) * 0.003, because we do * first in solidity
    feeAmount = FullMath.mulDivRoundingUp(amountIn, feePips, 1e6 - feePips);
```

3. deduct feed and calculated amountIn from `state.amountSpecifiedRemaining`

```solidity
if (exactInput) {
    state.amountSpecifiedRemaining -= (step.amountIn + step.feeAmount).toInt256();
    state.amountCalculated = state.amountCalculated.sub(step.amountOut.toInt256());

if (exactIn && sqrtRatioNextX96 != sqrtRatioTargetX96) {
    // we didn't reach the target, so take the remainder of the maximum input as fee
    feeAmount = uint256(amountRemaining) - amountIn;
```
