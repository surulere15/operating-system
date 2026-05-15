# Top 10 DeFi Protocols (February 2026)

This document provides a snapshot of the leading DeFi protocols to assist JOE with vulnerability mapping.

| Rank | Protocol | Category | TVL (Approx) | Key Innovation/Surface |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Lido** | Liquid Staking | $36.1B | Multi-chain staking, stETH liquidity. |
| 2 | **Aave** | Lending | $34.7B | Flash loans, multi-asset collateral pools. |
| 3 | **EigenLayer** | Restaking | $10.5B | Stake-sharing security, AVS ecosystem. |
| 4 | **Sky (MakerDAO)** | Stablecoin/Lending | $7.9B | DAI/USDS issuance, RWA integration. |
| 5 | **Ethena** | Delta-Neutral | $12.9B | USDe stablecoin, basis trade arbitrage. |
| 6 | **Morpho** | Lending | $4.2B | Vault V2, Oracle-agnostic markets. |
| 7 | **Spark** | Lending | $5.1B | Sky ecosystem integration, liquid restaking. |
| 8 | **Ether.fi** | Liquid Restaking | $13.0B | Non-custodial staking, DVT adoption. |
| 9 | **Pendle** | Yield Trading | $8.9B | Principal/Yield token splitting. |
| 10 | **Hyperliquid** | Perp DEX | $24.7B (Vol) | L1 chain, order-book based scaling. |

## Vulnerability Surfaces to Monitor

1.  **Oracles**: Prices for low-liquidity assets in Aave/Compound.
2.  **Flash Loans**: Arbitrage loops and governance manipulation.
3.  **Bridge Risk**: Cross-chain asset minting in Lido/Ether.fi.
4.  **Contract Upgrades**: Centralization risk in admin multi-sigs.
5.  **Hooks (Uniswap)**: Custom logic vulnerabilities in V4/V5.
