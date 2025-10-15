# verifiableStream

Scaffold for Verifiable Data Streaming (VDS) with two interchangeable schemes:

- VDS-CVC: Tree + Chameleon Vector Commitment (Construction 3)
- VDS-ACC: Signature + Bilinear Accumulator (Construction 4)

Status: This repository currently provides a minimal, runnable skeleton with
interfaces, CLI stubs, and tests marked skipped. Pairing-based cryptographic
implementations (charm-crypto) are not included in the scaffold and will be
added in subsequent iterations.

Layout
- vds/common: shared utilities (PRF, signatures, encoding, serialization)
- vds/cvc: CVC primitives and VDS wrapper (skeleton)
- vds/acc: accumulator primitives and VDS wrapper (skeleton)
- vds/storage: in-memory store (working) and file store (skeleton)
- vds/cli: CLI stub `vds_cli.py`
- tests: pytest stubs (most skipped until crypto is ready)
- bench: benchmark stubs

CLI
  python -m vds.cli.vds_cli --help

Python
  import vds
  from vds.storage.memstore import MemStore

Requirements
See requirements.txt. Pairing functionality requires installing charm-crypto.

