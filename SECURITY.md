# Security Policy

## Scope

This repository contains:
- a read-only public dashboard (`web/server.py`)
- an optional, immutable registry contract (`contracts/AXFOXRegistry.sol`)

Neither component holds funds, requests wallet signatures from visitors,
or has any privileged/admin functionality.

## Reporting a vulnerability

If you find a security issue in the dashboard code or the registry
contract, please open a GitHub issue on this repository, or reach out via
the contact channel listed on the live dashboard once configured.

Please do not disclose contract vulnerabilities that could be exploited
before there's a chance to review them — give a reasonable window for a
fix or a public acknowledgment that the report was received.

## What this project will never ask for

- your private key
- your seed / recovery phrase
- an unlimited token approval
- a wallet signature outside of a transaction you initiated yourself and
  can fully review in your wallet before approving
