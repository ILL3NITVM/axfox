# Contracts

## AXFOX token (canonical)

- Address: `0x3ABFBDf7a12Cb7589a330A293e91380f84A94444`
- Network: BNB Smart Chain (chain id 56)
- Standard: BEP-20 / ERC-20 compatible
- Launched via Four.meme's bonding-curve mechanism
- Decimals: 18
- Total supply: 1,000,000,000 AXFOX

This is the token contract — the thing DappBay and other directories
should list as the "Token Contract."

## AXFOXRegistry (optional, not required)

- Address: not deployed as of this writing — see `docs/DEPLOY_REGISTRY.md`
- Purpose: immutable, read-only project-identity registry only
- Explicitly excluded by design: custody, trading, token approvals,
  upgrades, admin/owner roles, any function that can move funds

If deployed and verified, this is a separate contract from the token —
some directories (e.g. DappBay) distinguish a general "project contract"
field from the "token contract" field. Never conflate the two, and never
enter an unrelated address (creator wallet, router, etc.) in either field.

## Derived on-chain facts (for transparency)

The Four.meme bonding-curve/sale contract for AXFOX was identified from
on-chain evidence, not guessed: it received the entire minted token
supply in the deployment transaction, is a genuine contract, and
currently holds the large majority of total supply as unsold inventory.
No PancakeSwap V2 pair exists yet (checked via a live `getPair()` call
against the canonical Factory contract) — AXFOX has not graduated from
the bonding curve.
