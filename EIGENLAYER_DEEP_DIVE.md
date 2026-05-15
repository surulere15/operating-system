# EigenLayer Deep Dive: Slashing Veto Committee & LRT Queues

## 1. Slashing Veto Committee Analysis
- **Composition**: Centralized at the entity level. The committee is comprised of members from the **Eigen Foundation** and **Eigen Labs**.
- **Member Status**: No public list of individual names/addresses. Power is ratified by the **Protocol Council** rather than direct EIGEN voting.
- **Risk**: **Concentrated Emergency Power**. A 9-of-13 multisig (reputed industry figures, but entity-aligned) holds the absolute power to veto slashing events. While intended as a safety buffer, it prevents the protocol from being truly permissionless and trustless in its current 2026 state.

## 2. LRT Withdrawal Queue Investigation
- **Visibility**: **Severe Lack of Transparency**. No public, real-time dashboards for withdrawal queue depth across major LRT providers (Ether.fi, Renzo, Puffer).
- **Liquidity Risk**: 
    - **DEX Exit**: Liquidity on DEXs (Curve/Uniswap) for Instant Exits is thin relative to total TVL.
    - **Market Stress**: In a de-pegging event, "Instant Exit" premiums spike, forcing users into on-chain unbonding queues.
- **Unpredictability**: Queue wait times are unpredictable in 2026, dependent on the underlying operator's unstacking speed and EigenLayer's 7-day withdrawal window.

## Recommendations
- **Avoid Over-Concentration**: Do not hold more than 15% of a portfolio in a single LRT if immediate liquidity is required.
- **Monitor Multisig**: Track the 9-of-13 multisig for any "emergency" veto activity.
