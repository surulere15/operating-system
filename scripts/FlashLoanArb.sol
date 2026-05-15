// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

import {FlashLoanSimpleReceiverBase} from "@aave/core-v3/contracts/flashloan/base/FlashLoanSimpleReceiverBase.sol";
import {IPoolAddressesProvider} from "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol";
import {IERC20} from "@aave/core-v3/contracts/dependencies/openzeppelin/contracts/IERC20.sol";

interface ISwapRouter {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 deadline;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }
    function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut);
}

contract FlashLoanArb is FlashLoanSimpleReceiverBase {
    address payable owner;
    ISwapRouter public immutable swapRouter;

    constructor(address _addressProvider, address _swapRouter)
        FlashLoanSimpleReceiverBase(IPoolAddressesProvider(_addressProvider))
    {
        owner = payable(msg.sender);
        swapRouter = ISwapRouter(_swapRouter);
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        // Security: Only allow this contract to initiate flash loans
        require(initiator == address(this), "Untrusted initiator");

        // 1. We have the borrowed `amount` of `asset` here.
        
        // 2. Decode params to get target arb path (Token A -> Token B -> Token A)
        (address tokenB, uint24 fee1, uint24 fee2) = abi.decode(params, (address, uint24, uint24));

        // 3. Trade 1: Asset -> Token B (Uniswap V3)
        IERC20(asset).approve(address(swapRouter), amount);
        ISwapRouter.ExactInputSingleParams memory swapParams1 =
            ISwapRouter.ExactInputSingleParams({
                tokenIn: asset,
                tokenOut: tokenB,
                fee: fee1,
                recipient: address(this),
                deadline: block.timestamp,
                amountIn: amount,
                amountOutMinimum: 0,
                sqrtPriceLimitX96: 0
            });
        uint256 amountB = swapRouter.exactInputSingle(swapParams1);

        // 4. Trade 2: Token B -> Asset (Uniswap V3 - or another DEX)
        // For simplicity in this template, we swap back on UniV3 but ideally this is another DEX.
        IERC20(tokenB).approve(address(swapRouter), amountB);
        ISwapRouter.ExactInputSingleParams memory swapParams2 =
            ISwapRouter.ExactInputSingleParams({
                tokenIn: tokenB,
                tokenOut: asset,
                fee: fee2,
                recipient: address(this),
                deadline: block.timestamp,
                amountIn: amountB,
                amountOutMinimum: amount + premium, // Fail if we don't cover loan + fee
                sqrtPriceLimitX96: 0
            });
            
        uint256 amountAssetBack = swapRouter.exactInputSingle(swapParams2);

        // 5. Repay Flash Loan
        uint256 totalDebt = amount + premium;
        require(amountAssetBack >= totalDebt, "Arb failed: Unprofitable");
        
        IERC20(asset).approve(address(POOL), totalDebt);

        // 6. Keep Profit
        uint256 profit = amountAssetBack - totalDebt;
        if (profit > 0) {
            // Optional: Auto-send profit to owner to avoid keeping funds in hot contract
            // IERC20(asset).transfer(owner, profit);
        }

        return true;
    }

    function requestFlashLoan(address _token, uint256 _amount, address _tokenB, uint24 _fee1, uint24 _fee2) public onlyOwner {
        address receiverAddress = address(this);
        address asset = _token;
        uint256 amount = _amount;
        bytes memory params = abi.encode(_tokenB, _fee1, _fee2);
        uint16 poolId = 0;

        POOL.flashLoanSimple(
            receiverAddress,
            asset,
            amount,
            params,
            poolId
        );
    }
    
    function withdraw(address _token) external onlyOwner {
        uint256 balance = IERC20(_token).balanceOf(address(this));
        require(balance > 0, "No balance");
        IERC20(_token).transfer(owner, balance);
    }

    function withdrawETH() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No ETH balance");
        (bool sent, ) = owner.call{value: balance}("");
        require(sent, "Failed to send Ether");
    }
}
