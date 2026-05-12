# 📚 ZimAgriTrust Documentation Index

This directory holds all canonical project documentation. Anything not listed here either lives at the repo root (`README.md`, `CLAUDE.md`, `LICENSE`, `QUICK_START.md`, `DEPLOYMENT_GUIDE.md`) or has been archived into `docs/archive/`.

## 🎯 Canonical documents

Read these in order to onboard:

| # | Document | Purpose |
|---|---|---|
| 1 | [`SYSTEM_SPECIFICATION.md`](./SYSTEM_SPECIFICATION.md) | The 348-function product spec. Source of truth for every feature, endpoint, screen, notification template. |
| 2 | [`ARCHITECTURE_STANDARD.md`](./ARCHITECTURE_STANDARD.md) | The layered Clean-Architecture standard (domain → application → infrastructure → api). All new code follows this. |
| 3 | [`SYSTEM_GAP_ANALYSIS.md`](./SYSTEM_GAP_ANALYSIS.md) | Per-function status (✅/🟡/🔴) measured against the spec. Updated each sprint. |
| 4 | [`SYSTEM_ROADMAP.md`](./SYSTEM_ROADMAP.md) | 10-sprint, ~20-week phased plan to close the gap. Every task linked back to a spec function ID. |
| 5 | [`DEAD_CODE_AUDIT.md`](./DEAD_CODE_AUDIT.md) | Audit findings + the cleanup that was performed. |

## 📁 Sub-directories

| Path | Contents |
|---|---|
| [`api/`](./api/) | API reference, OpenAPI snapshots |
| [`guides/`](./guides/) | Developer + deployment guides |
| [`system/`](./system/) | System-level analyses (admin panel, command center, …) |
| [`training/`](./training/) | Agent training manual + walkthroughs |
| [`archive/`](./archive/) | Historical snapshots — `*_COMPLETE.md`, `*_PLAN.md`, `CODEBASE_ANALYSIS_*.md`, `IMPLEMENTATION_*.md`, `SECURITY_AUDIT_*.md`, `ENTERPRISE_*.md`, etc. Kept for context; **not** authoritative. |

## 📄 Older long-form docs

These predate the canonical set and remain for now:

- `AgriTrust_Full_Documentation.md`
- `AgriTrust_Master_Documentation_v4.0.md`

They will be folded into the canonical docs over time.

## 🧭 Top-level files (repo root)

| File | Purpose |
|---|---|
| `README.md` | Project overview, quickstart |
| `CLAUDE.md` | Pair-programming context for Claude Code agents |
| `QUICK_START.md` | "Get the stack running in 5 minutes" guide |
| `DEPLOYMENT_GUIDE.md` | Production deployment instructions |
| `LICENSE` | License |

Everything else that used to be at the root has been archived.
