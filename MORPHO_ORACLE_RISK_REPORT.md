# Morpho Blue: Oracle & Permissionless Risk Analysis (Feb 2026)

## 1. Market Parameterization
Every Morpho Blue market is defined by a unique `MarketId` derived from five immutable parameters:
- **Collateral Asset**: Must be ERC20.
- **Loan Asset**: Must be ERC20 (non-ERC4626).
- **LLTV (Liquidation Loan-To-Value)**: A fixed percentage (e.g., 90%). Permanent at market birth.
- **Oracle**: A contract implementing `price()` (1 unit of Collateral in units of Loan Asset).
- **IRM (Interest Rate Model)**: Usually `AdaptiveCurveIRM` for autonomous rate discovery.

---

## 2. Permissionless Creation Risks

### "Oracle-as-an-Asset" Attack
- **Vulnerability**: Since anyone can create a market with any `OracleAddress`, a malicious actor can deploy an oracle they control.
- **Execution**: The attacker supplies a worthless token as collateral, points the market to their malicious oracle which reports a high price, and borrows the entire liquidity of the loan asset (e.g., USDC or WETH).
- **Countermeasure**: Passive lenders must **never** deposit into markets where the Oracle address is not audited or managed by a reputable curator (e.g., Gauntlet, Block Analitica).

### Decimal & Scaling Mismatch
- **Vulnerability**: The `price()` function must scale the output to account for decimal differences between the collateral and loan assets.
- **Historical Context**: The 2024 PAXG/USDC exploit ($230K) was caused by a `SCALE_FACTOR` mismatch where the oracle inflated the collateral's value by 10¹².
- **2026 Status**: While reference implementations like `MorphoChainlinkOracleV2` mitigate this, custom oracles for exotic RWAs (Real World Assets) remain the primary vector for loss of funds.

### Isolation vs. Contagion
- **Isolation Benefit**: A failure in a `PEPE/USDC` market cannot drain funds from a `wstETH/USDC` market.
- **Vault Contagion**: Systemic risk re-enters through **MetaMorpho Vaults**. If a vault curator whitelists a market with a faulty/malicious oracle, everyone in that vault is exposed.

---

## 3. Technical Safeguards
- **Immutable Logic**: Once a market ID is generated, the parameters cannot be "upgraded" or changed. This prevents "late-stage" oracle hijacking by governance.
- **Adaptive Curve IRM**: Protects against interest rate manipulation by autonomously adjusting the target utilization to 90%.

## 4. Final Recommendation for JOE
When auditing protocol deployments:
1.  **Cross-reference** `OracleAddress` in `MarketId` against the known reference implementations in the `morpho-blue-oracles` repository.
2.  **Verify** the `LLTV` is within the "Standard" range (usually < 94.5% for liquid assets).
3.  **Audit MetaMorpho Allocations**: Ensure the `supplyQueue` only contains markets with reputable curators.
