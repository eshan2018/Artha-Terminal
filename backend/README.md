# `backend/` — the layered application

This tree realizes the L0–L10 stack of
[docs/architecture/03-system-architecture.md](../docs/architecture/03-system-architecture.md).
Boundaries are **CI-enforced** by [`tools/ci`](../tools/ci) — an upward import, a vendor name
above L1, or a cross-module schema read **fails the build**. The rules live in one place:
[`tools/ci/architecture_map.py`](../tools/ci/architecture_map.py).

> **M1 status:** this is the Phase 0 *skeleton*. Packages are empty (docstrings only) except
> for the guardrails and their tests. **No feature code exists yet** (per doc 15 Phase 0).

## Module → layer → owning document (one owner each)
| Package | Layer | Owning doc(s) | May import |
|---------|-------|---------------|------------|
| `platform` | kernel | 02, 04 | (nothing internal) |
| `providers.ports` | L1 | 06 | `platform` |
| `providers` (adapters) | L1 | 06 | `platform`, `providers.ports` |
| `ingestion` | L2–L4 | 05 | `platform`, `providers.ports`, `domain.model` |
| `domain.model` | L4/L5 | 04 | `platform` |
| `domain` (repositories) | L5 | 04, 07 | `platform`, `domain.model` |
| `features` | L6 | 08 | `platform`, `domain.model`, `domain` |
| `analytics` | L7 | 08 | `platform`, `domain.model`, `features` |
| `api` | L9 | 10 | `platform`, `domain.model`, `analytics` |
| `orchestration` | coordinator | 16 | the layers it drives (below it) |

Notes:
- **`platform`** (kernel) is importable everywhere; a package may always import its own subpackages.
- **`features` is the only layer with repository access** (doc 08); analytics consumes features
  and other engines' results, never repositories.
- **Data-owning modules under `domain/`** (e.g. `domain/market_data`) own their schema and must
  not read each other's internals (ADR-0003); `domain/model` is shared vocabulary and is exempt.
- **Vendor names** (e.g. `yfinance`) may appear only under that vendor's adapter package
  (`providers/yfinance`) — doc 06 / ADR-0005.

## Running the gate
```
make install   # into the active venv: pip install -e ".[dev]"
make check     # architecture guardrails + ruff + pytest (the CI gate)
```
Individual steps: `make lint-arch`, `make lint`, `make test`.

Changing a layer boundary is changing the architecture — it requires an **ADR**, not an edit to
`architecture_map.py` alone.
