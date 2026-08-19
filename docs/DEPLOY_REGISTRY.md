# Deploying AXFOXRegistry.sol

**Not deployed yet — this is a human decision.** Claude will not deploy
this contract; it requires a wallet signature only the project owner can
give. This document is instructions for *you* to do it, or to decide not
to.

## What it does

A tiny, immutable, read-only registry: it stores the canonical AXFOX token
address and a few metadata strings (name, ticker, version, website) at
construction time and never changes them again. It cannot hold BNB, cannot
call the token contract, cannot approve/transfer anything, and has no
admin/owner functions. See the contract source and its NatSpec comments in
`contracts/AXFOXRegistry.sol` for the exact scope.

## Deploy via Remix (simplest, no local toolchain needed)

1. Open <https://remix.ethereum.org>.
2. Create a new file, paste in `contracts/AXFOXRegistry.sol`.
3. Compile with Solidity `^0.8.24`.
4. In the "Deploy & Run Transactions" tab, set **Environment** to
   "Injected Provider - MetaMask" and make sure MetaMask is on **BNB Smart
   Chain** (chain id 56).
5. Fill in the constructor arguments:
   - `_token`: `0x3ABFBDf7a12Cb7589a330A293e91380f84A94444`
   - `_projectName`: `AxolotlFox`
   - `_ticker`: `AXFOX`
   - `_version`: `1`
   - `_officialWebsite`: (your public dashboard URL, once hosting is set up)
6. Click **Deploy**. MetaMask will prompt you to review and sign the
   deployment transaction — review the gas cost and contract data before
   approving. This is the only place a signature is needed.
7. Copy the deployed contract address.

## After deployment

1. Verify the source on BscScan (Contract → Verify and Publish). Since
   this is single-file with a simple constructor, "Solidity (Single file)"
   verification should work directly with the source above and the exact
   constructor argument values.
2. Only once verified, enter this address in DappBay's **Contracts**
   field. The AXFOX **token** contract
   (`0x3ABFBDf7a12Cb7589a330A293e91380f84A94444`) stays in DappBay's
   **Token Contract** field — they're different fields for different
   things.

## If you decide not to deploy it

That's a completely reasonable call — DappBay's "Contracts" field may not
be strictly required, or you may prefer to submit without it and see what
the form actually validates. Nothing else in this project depends on this
contract existing.
