# Ethena Security Audit Report (Feb 2026)

## Summary
Security audit of Ethena (Rank 5 DeFi Protocol). Focus on USDe stability, the 24/7 off-chain delta-neutral hedging engine, and the robustness of the Reserve Fund after the 2025 market stress tests.

## High-Risk Surfaces

### 1. Delta-Neutral Basis Risk
- **Mechanism**: USDe is backed by staked assets (stETH) and offsetting short perpetual positions on CEXs.
- **2026 Risk**: During the October 2025 deleveraging event, the basis (difference between spot and futures prices) diverged significantly, causing temporary de-pegs in low-liquidity pools. A prolonged period of "backwardation" (futures trading below spot) would force the protocol to pay funding, eroding the Reserve Fund.

### 2. CEX Counterparty Exposure
- **Vulnerability**: Ethena's delta-neutral strategy relies heavily on centralized exchanges (Binance, Bybit, OKX) for its short legs.
- **Observation**: The protocol uses "Off-Exchange Settlement" providers to minimize custodial risk, but is still exposed to the insolvency or operational failure of the underlying CEXs. The 2025 Bybit security incident triggered a 4-hour "hedging freeze" for USDe.

### 3. Oracle Lag & Slippage
- **Mechanism**: Automated hedging relies on sub-second price feeds and liquidity in CEX perpetual markets.
- **2025 Finding**: During the $19B flash crash, oracle lag between on-chain USDe prices and CEX perpetual prices led to an "arbitrage latency" where the hedging engine could not react fast enough, causing a temporary 1.2% deviance below the $1 peg.

## Safeguards & mitigations
- **Reserve Fund (Insurance)**: Post-2025, the Reserve Fund was bolstered to $450M to handle extended negative funding environments.
- **Monitoring**: Implemented a 24/7 "Flash Hedge" protocol to prioritize peg stability over funding efficiency during high volatility.

## Systemic Threats
- **Redemption Congestion**: Retail users lack direct redemption rights and must use secondary markets. In a liquidity crisis where CEXs pause withdrawals, USDe holders could be trapped in de-pegging liquidity pools on-chain.
