# AxolotlFox — AXFOX 🦎🦊

Half axolotl. Half fox. A community meme token on **BNB Smart Chain**,
launched through [Four.meme](https://four.meme).

**Token contract:**
`0x3ABFBDf7a12Cb7589a330A293e91380f84A94444`

**Creator public wallet:**
`0x203f3D9E101a8A2ADb4c49652eFB1240174a5569`

**No guaranteed returns.** This is an early-stage, speculative meme token.
Nothing here is investment advice.

## Token

| | |
|---|---|
| Name | AxolotlFox |
| Ticker | AXFOX |
| Network | BNB Smart Chain (chain id 56) |
| Contract | `0x3ABFBDf7a12Cb7589a330A293e91380f84A94444` |
| Creator wallet (public) | `0x203f3D9E101a8A2ADb4c49652eFB1240174a5569` |
| Launched via | Four.meme (bonding curve) |

**Verify the contract yourself** on [BscScan](https://bscscan.com/token/0x3ABFBDf7a12Cb7589a330A293e91380f84A94444)
before doing anything.

## What's in this repo

- `web/` — the public read-only AXFOX dashboard (`server.py`, stdlib Python
  only). Shows live holder counts, bonding-curve state, and system status —
  nothing fabricated; unavailable data is labeled `UNAVAILABLE`, not hidden
  or guessed.
- `contracts/AXFOXRegistry.sol` — an optional, immutable, read-only
  registry contract (not deployed by default — see
  `docs/DEPLOY_REGISTRY.md`). No custody, no trading, no admin functions.
- `docs/` — deployment and process notes.
- `assets/` — logo/media.

## Security boundaries

- This project has **no wallet-signing automation**. Every transaction
  (contract deployment, DappBay submission, anything requiring a
  signature) is a manual, human-reviewed action.
- The dashboard (`web/server.py`) is strictly read-only — it renders chain
  state, it never writes to the chain or requests a wallet connection from
  visitors.
- No private key, seed phrase, or recovery phrase is ever requested,
  stored, or transmitted anywhere in this repository or its tooling.

See `SECURITY.md` for the vulnerability-disclosure process.

## No guaranteed return

AXFOX is an early-stage, speculative meme token. Nothing here is
investment advice, and there is no guarantee of value, liquidity, or
return. Independent holder counts and market data are reported honestly,
including when the answer is "not much has happened yet."
