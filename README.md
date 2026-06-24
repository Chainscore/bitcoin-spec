# Bitcoin Protocol Specification

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/bitcoin-core-code-cover-dark.png">
  <img alt="Bitcoin Protocol Specification cover" src="assets/bitcoin-core-code-cover-light.png">
</picture>

In this specification for the Bitcoin protocol, we have covered most of the concepts & rulesets to develop on Bitcoin: consensus rules,
transaction and block formats, canonical serialization, Bitcoin Script opcode
behavior, UTXO state transitions, proof-of-work chain selection, mempool relay
boundaries, and peer-to-peer network messages.

The specification is maintained as a buildable PDF and LaTeX source. It cites
BIPs, Bitcoin Core source evidence, and deployed full-node behavior.

The document does not change Bitcoin consensus rules. It is a maintained
technical reference that distinguishes consensus rules, peer-service behavior,
mempool behavior, and implementation evidence.

The current draft baseline is Bitcoin Core 31.0. BIPs are incorporated only when
they are live in that full-node baseline.

Bitcoin protocol specification, Bitcoin consensus rules, Bitcoin Core
consensus, Bitcoin transaction format, Bitcoin block format, block validation,
UTXO set, Bitcoin Script opcodes, Taproot, Tapscript, SegWit, proof of work,
mempool policy, Bitcoin P2P network protocol, BIP reference.

## Read the specification

The canonical generated PDFs are:

- `out/protocol.pdf`
- `out/protocol-dark.pdf`

The main source file is `protocol.tex`; section sources live under `sections/`.

## Scope

This repository is intended for developers, protocol engineers, researchers,
client implementers, infrastructure teams, and reviewers who need a compact
source of truth for Bitcoin protocol behavior.

Covered areas include:

- notation, hashes, identifiers, and canonical encodings;
- transaction records, transaction identifiers, locktime, and sequence locks;
- Script execution, signature messages, and opcode classes;
- block records, Merkle roots, witness commitments, and contextual block checks;
- compact target encoding, difficulty adjustment, proof of work, and chainwork;
- active-chain validation, UTXO transitions, reorganization correctness, and
  consensus rule context;
- mempool admission as local relay state; and
- interoperable P2P message behavior.

Out of scope: wallet UX, address-book behavior, mining interfaces, exchange
policy, historical proposal tracking, and Bitcoin Core RPC manuals.

## Build dependencies

On Debian-based systems, install at least:

```sh
apt install make git latexmk texlive texlive-latex-extra texlive-fonts-recommended
```

## Building

```sh
make protocol
make protocol-dark
make all
```

The outputs are written to:

```text
out/protocol.pdf
out/protocol-dark.pdf
```

Intermediate files are written to `aux/`. The generated `protocol.ver` file and
`aux/` directory are ignored by Git.

## Contribution rules

- Cite source material for every normative claim.
- Keep consensus rules separate from local mempool admission and relay behavior.
- Mark implementation-observed behavior explicitly when it is not specified by
  a deployed or complete BIP.
- Do not fold draft BIPs into active protocol behavior.
