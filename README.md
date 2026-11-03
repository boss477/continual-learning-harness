# Codex Memory Layer

Phase 1 defines the storage and benchmark contract for a bounded memory layer used with Codex.

## Tiers

- **T0**: disposable session evidence. It is size- and age-limited.
- **T1**: candidate memories awaiting replay and promotion.
- **T2**: compact, approved repository rules exported as `MEMORY.md`.

## Storage guarantees

The implementation must enforce these limits:

- T0: 7 days and 500 MiB, whichever is reached first.
- T1: 100 candidates.
- T2: 200 rules and 50 KiB for the exported memory.
- Rejected and superseded records are deleted unless explicitly exported for a benchmark artifact.

The limits are hard caps, not cleanup targets. A write that would exceed a cap must evict according to the policy before committing.

## Benchmark contract

The benchmark adapter will generate:

```text
/memory/MEMORY.md
/memory/manifest.json
```

`MEMORY.md` must be self-contained and concise. `manifest.json` records the memory byte count, rule count, source episode count, and generator configuration without storing raw trajectories.

## Planned phases

1. Contract, schema, and bounded retention policy.
2. Wake-phase episode collector.
3. Sleep-phase candidate generation.
4. Replay verifier and promotion gates.
5. Codex/MCP loading adapter.
6. FrontierMemory adapter and three-run benchmark report.
