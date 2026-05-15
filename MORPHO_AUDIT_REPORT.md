# Morpho Security Audit Report (Feb 2026)

## Summary
Audit of Morpho (Rank 6 DeFi Protocol). Investigation into **Morpho Blue** (modular lending primitive) and **MetaMorpho** (risk curation layer). Focus on oracle-agnostic vulnerabilities and curator trust models in 2026.

## High-Risk Surfaces

### 1. Oracle Misconfiguration (Decimal Mismatch)
- **Mechanism**: Morpho Blue is oracle-agnostic; market creators can use any price feed. 
- **2026 Risk**: The protocol remains susceptible to human error in oracle deployments. The 2024 PAXG/USDC exploit ($230K) resulted from a 12-decimal mismatch in a custom oracle calculation.
- **Observation**: While standard MetaMorpho vaults use audited oracles (Chainlink/Pyth), permissionless markets created outside these vaults offer significantly higher risk for liquidity suppliers.

### 2. Curator Centralization & MetaMorpho Risks
- **Mechanism**: MetaMorpho curators (Owner, Curator, Allocator) manage capital allocation across markets.
- **Vulnerability**: If a vault curator is compromised or acts maliciously, they can reallocate capital to a market with a "bad" oracle (e.g., an oracle they control that overestimates collateral value), effectively draining the vault.
- **Mitigation**: Morpho Vault V2 uses **timelocks (up to 3 weeks)** and **Sentinels** to revoke malicious proposals, but these require active 24/7 monitoring by vault participants.

### 3. Oracle Aggregator Lags
- **Finding**: Oracle-agnostic markets often use TWAP or custom aggregators to avoid Chainlink fees. During the 2025 "Flash Deleveraging," several Morpho Blue markets experienced 2-4% oracle lag relative to CEX prices, leading to bad debt in under-collateralized pools.

## Safeguards & mitigations
- **Formal Verification**: Morpho remains one of the most rigorously formally-verified protocols in DeFi. 
- **In-Kind Redemptions**: MetaMorpho shares can sometimes be redeemed "in-kind" (raw collateral/loan positions) if liquidity is unavailable, protecting against standard "bank run" scenarios.

## Systemic Threats
- **Shared Liquidity Contagion**: While markets are isolated, MetaMorpho vaults often aggregate multiple markets. A single failed market within a vault's supply queue can impact the entire vault's NAV.
