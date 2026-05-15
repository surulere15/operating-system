# Sky Deep Dive: SSR Mechanics & USDS Backing (2026)

## 1. Sky Savings Rate (SSR) Mechanics
The SSR is the primary incentive for holding USDS. It is a variable yield paid to USDS holders who deposit into the Savings module.

### Core Parameters (Feb 2026):
- **Current Rate**: **4.5% APY** (Stabilized from the 2025 "Endgame" launch peaks of 9.5%).
- **Yield Token**: **sUSDS** (A non-rebasing, yield-bearing ERC-20). Its redemption value increases hourly relative to USDS.
- **Liquidity**: No lockup periods or withdrawal fees.
- **Interoperability**: sUSDS is fully compatible with major DeFi lending markets (Aave, Spark).

---

## 2. USDS Collateral Backing
USDS is an overcollateralized stablecoin, meaning its value is backed by a surplus of assets held in decentralized "Sky Vaults."

### Collateral Mix:
- **Tokenized RWA (60%)**: Primarily U.S. Treasury bills (BUIDL, Flux, Superstate), corporate credit, and specialized lending facilities (HVBank).
- **Decentralized Assets (30%)**: ETH, wstETH, and WBTC.
- **Stability Peg Assets (10%)**: USDC and USDT held in the Peg Stability Module (PSM).

### Risk Management:
- **Target Collateralization Ratio**: Minimum **150%** for crypto-collateralized vaults.
- **Stability Buffer**: A protocol-owned reserve fund that absorbs minor depeg events and bad debt without impacting SSR payouts.
- **Auto-Liquidation**: On-chain oracles trigger collateral auctions if the value falls below the safety threshold.

---

## 3. Governance Levers & Sustainability
Sky Governance (SKY stakers) controls the economic parameters of the system through decentralized voting.

- **Rate Adjustment**: Governance actively adjusts the SSR to balance USDS supply and demand. If USDS supply is too high (excessive leverage), the SSR is lowered; if too low, it is raised.
- **Smart Burn Engine**: Protocol revenue is used to buy back and burn SKY tokens to reward long-term governance participants.
- **Endgame State**: Core mechanisms are now largely automated, with major risk parameters governed by specialized **Sky Stars (SubDAOs)** to prevent organizational bottlenecks.

---

## 4. Security & Compliance (2026)
- **MiCA Compliance**: USDS is designed for full compatibility with the EU's Markets in Crypto-Assets (MiCA) framework, facilitating institutional adoption.
- **Upgradeability**: Unlike DAI, USDS is an upgradeable contract. This allows for rapid security patches but requires a higher degree of trust in the **Sky Council** multisig.
- **Oracle Reliance**: Stability depends on accurate price feeds for both crypto and tokenized RWA.

---

## 5. Summary Verdict
The Sky ecosystem in 2026 has successfully transitioned into a **yield-generating DeFi infrastructure**. While the move to RWA reduces crypto-native volatility, the **upgradeability of USDS** and the **centralization of RWA custodians** remain the primary systemic risks. The 4.5% SSR is sustainable under current market conditions but remains sensitive to U.S. interest rate shifts.
