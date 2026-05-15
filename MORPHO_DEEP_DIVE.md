# Morpho Vault V2 Deep Dive: Security & Noncustodial Guarantees

## 1. Role-Based Access Control (RBAC)
Morpho Vault V2 features a strict separation of powers to prevent a single compromised address from draining funds:

- **Owner**: Manages roles (adding/removing Curators or Sentinels) and global vault parameters.
- **Curator**: Proposes the risk strategy (which markets to use and their caps).
- **Allocator**: Executes allocations within the caps set by the Curator.
- **Sentinel**: The emergency safety role. Can only **reduce** risk (lower caps, revoke pending actions, or force deallocations).

---

## 2. Granular Timelocks
Unlike V1's global timelock, V2 uses **per-function timelocks** (0 to 3 weeks):

- **Security Benefit**: Actions that increase security (like increasing a timelock or lowering a cap) take effect **instantly**.
- **User Protection**: Actions that decrease security (like lowering a timelock or increasing a cap) must wait for the configured delay.
- **Abdication**: Curators can `abdicate` a function, permanently disabling it to provide irreversible trust guarantees.

---

## 3. Sentinel Safeguards
The Sentinel is the "Active Defense" layer of the vault:
- **Revocation**: Can instantly cancel any pending Curator proposal during its timelock period.
- **De-risking**: Can lower market caps immediately if a vulnerability is detected.
- **Non-Custodial Design**: A malicious Sentinel **cannot** steal funds or increase risk; they can only force the vault into a "safe" (deallocated) state.

---

## 4. In-Kind Redemption (The Escape Hatch)
This is the ultimate guarantee against permanent lock-in or "honoring" bad oracles:
- **Mechanism**: The `forceDeallocate` function allows anyone (curators, sentinels, or even users via flash loans) to withdraw assets from an illiquid market back to the vault's idle pool.
- **Penalty**: A capped **2% fee** is charged on forced deallocations to prevent griefing, but it ensures users can always exit even if the Curator is unresponsive or markets are frozen.
- **Result**: Even in the event of a total Curator failure, users can reclaim their underlying assets noncustodially.

---

## 5. Security Verdict (2026)
MetaMorpho Vault V2 represents the state-of-the-art in **Risk-Managed Lending**. While Oracle misconfiguration (on the Morpho Blue layer) remains the primary threat, the Vault V2 architecture ensures that passive lenders have:
1.  **Advance Notice** of all risky changes.
2.  **Emergency Override** capabilities via Trusted Sentinels.
3.  **Guaranteed Exit Paths** via in-kind redemption.
