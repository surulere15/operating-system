# Spark Security Audit Report (Feb 2026)

## Summary
Audit of Spark (Rank 7 DeFi Protocol), a primary SubDAO of the **Sky Protocol** (formerly MakerDAO). Focus on its role as a liquidity layer for sUSDS/sDAI and its systemic exposure to external yield sources like Ethena.

---

## 1. Technical Architecture & Governance
- **SubDAO Status**: Spark operates as a "Star SubDAO." While it has its own token (SPK), its core risk parameters and code upgrades are managed via **Sky Governance**.
- **Governance Relay**: Uses a specialized relay (audited by ChainSecurity) to execute proposals across chains (Ethereum, L2s).
- **Core Components**:
    - **SparkLend**: Non-custodial lending primitive (Aave V3 fork).
    - **Spark Liquidity Layer (SLL)**: Routes idle stablecoins into high-yield venues.
    - **sUSDS/sDAI**: Receipt tokens for the Sky Savings Rate (SSR).

---

## 2. Key Risk Vectors (2026)

### Centralization & Upgradeability
- **USDS Backdoor**: Unlike the original DAI, the **USDS stablecoin contract is upgradeable**. This introduces a centralized point of failure where governance or a compromised multisig could theoretically freeze funds or implement "emergency" logic changes.
- **Off-chain Signers**: Reliance on centralized signers for USDS and CCTP cross-chain movements remains a core trust assumption.

### Systemic Exposure (Ethena Basis Risk)
- **$1.1 Billion Allocation**: Spark has allocated significant capital to **Ethena’s USDe and sUSDe**. 
- **Risk**: During a severe market downturn or a "negative funding rate" environment for Ethena, Spark's yield could collapse, potentially impacting USDS stability or the Reserve Fund's ability to cover bad debt.

### Governance "Endgame" Dynamics
- **Star SubDAO Independence**: Current governance is entity-centralized under the Sky Core Council. The transition to fully autonomous SubDAOs is still in progress, leaving Spark vulnerable to "Governance Capture" from the parent protocol.

---

## 3. Security Status
- **Audits**: Last major audit (Oct 2024) by ChainSecurity. **No critical vulnerabilities** found in the ALM Controller or sDAI oracles.
- **Insurance**: Protected by **Nexus Mutual Protocol Cover** (for sDAI/sUSDS), which covers smart contract exploits but **not USDS depegging**.

---

## 4. Final Verdict
Spark is a highly robust and audited lending market, but in 2026, it serves as the primary **Risk Conduit** for the MakerDAO/Sky ecosystem. Its safety is entirely dependent on:
1.  **USDS Centralization**: Trust in Sky's upgradeability management.
2.  **External Counterparties**: Stability of Ethena ($1.1B exposure).
3.  **RWA Integrity**: The quality of off-chain collateral backing the underlying USDS.
