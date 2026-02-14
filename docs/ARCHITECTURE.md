# Architecture (MVP)

## Flow
1. Ingest listings from Datafiniti.
2. Enrich with Estated (deed history + AVM + property facts).
3. Store raw + normalized data in SQLite.
4. Build comps from recent sales within radius + sqft band.
5. Underwrite (discount %, ARV, condition score placeholder).
6. Alert by email if threshold hit.

## Key constraints
- No MLS access.
- Low budget, minimal infrastructure.
- Alert latency depends on vendor refresh rates.

## Next steps
- Add retry + backoff for ingestion.
- Introduce queueing for photo analysis.
- Add monitoring (run logs + failures).
