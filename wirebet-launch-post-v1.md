# Wirebet — On-Chain Binary Prediction Markets on Base

**The future of information markets is on-chain.**

---

## What Is Wirebet?

Wirebet is a fully on-chain binary prediction market protocol deployed on Base. Traders buy YES/NO shares on real-world outcome questions, with prices set by a **Logarithmic Market Scoring Rule (LMSR)** automated market maker.

No off-chain orderbook. No backend database. No centralized API. All trading, pricing, and settlement happens on-chain.

**Core thesis:** Prediction markets are the most capital-efficient mechanism for aggregating distributed information into a single price signal.

---

## Why This Matters

Prediction markets have a 30-year academic track record of producing better forecasts than expert panels, polling, or media analysis. Robin Hanson's work on "idea futures" has been validated across every domain from elections to pandemic response.

The problem: existing prediction markets are either:
- **Centralized** (Polymarket, Kalshi) — subject to regulatory risk, single points of failure, and take rates of 5-12%
- **Broken** (Augur, Gnosis) — UX disasters that never achieved meaningful adoption

Wirebet solves the adoption problem with institutional-grade infrastructure on a low-fee L2.

---

## Technical Highlights

| Feature | Implementation |
|---------|---------------|
| Pricing engine | LMSR (mathematically proven, no counterparty needed) |
| Chain | Base (EVM-compatible L2) |
| Smart contracts | 8 Solidity contracts, Foundry-tested |
| Security | ReentrancyGuard, Pausable, SafeERC20, slippage protection |
| Frontend | Next.js 16, React 19, Tailwind v4, RainbowKit |
| Data | 100% on-chain, zero backend dependency |
| Fee model | 1% trading fee (configurable per-market) |

---

## Live Markets

Currently deployed on **Base Sepolia** testnet. Markets are live and tradeable with testnet ETH.

[View Live Demo](https://wirebet.xyz) — Connect wallet, create a market, place a trade.

---

## Market Opportunity

- **Polymarket** did $1B+ in 2024 volume with centralized infrastructure
- **Kalshi** received CFTC approval for event contracts in the US
- The global prediction/gambling market is **$500B+** and growing

DeFi-native prediction markets capture value through:
1. **Lower fees** (1% vs 5-12% centralized)
2. **Permissionless market creation** (anyone can list anything)
3. **Censorship resistance** (no entity can shut down markets)
4. **Composability** (markets integrate with DeFi — lending, AMMs, vaults)

---

## Revenue Model

| Stream | Mechanism |
|--------|-----------|
| Trading fees | 1% per trade (protocol revenue) |
| Market creation | Zero cost, drives volume |
| Premium features | API access, analytics dashboards |
| Liquidity provision | Vault4626 enables passive yield |

---

## Team & Ecosystem

Built as part of a broader AI + DeFi intelligence infrastructure ecosystem including:
- DeAI compute market intelligence
- DeFi security auditing toolkit
- Regulatory compliance automation
- Trading signal SaaS

Wirebet is the **market mechanism layer** — the interface between information and capital.

---

## Roadmap

- [x] Core protocol (LMSR AMM, factory, positions, vault, fees)
- [x] Trading terminal UI with real-time charting
- [x] Admin/resolver dashboard
- [x] Server-persisted metadata
- [ ] Mainnet deployment (pending audit + funding)
- [ ] Chainlink/UMA oracle integration for automated resolution
- [ ] Liquidity mining program
- [ ] Mobile-responsive redesign
- [ ] Cross-chain expansion (Arbitrum, Optimism)

---

## Call to Action

**Test it now:** Deploy a market on Sepolia. Place a trade. See how on-chain prediction markets should work.

**Build with us:** Integrate Wirebet markets into your application via our open API.

**Invest:** If you believe information markets are the next trillion-dollar DeFi primitive, let's talk.

---

*Wirebet — Where information becomes price.*