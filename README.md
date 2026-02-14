# flip_scrape

MVP pipeline to ingest non-MLS property listings for Long Island (Nassau + Suffolk), underwrite fix-and-flip deals, and alert on undervalued opportunities.

## MVP Data Path (no MLS access)
- Listings + listing history: Datafiniti Property Data
- Property facts + deed history + AVM: Estated Property Data

## Quick start
1. Create `config/.env` from `config/example.env` and set API keys.
2. Adjust thresholds in `config/criteria.json`.
3. Run the pipeline:

```bash
python -m src.pipeline
```

## Notes
- This repo is intentionally minimal and API-first. Real production usage will need stronger data QA, retries, and monitoring.
- No MLS data is used or scraped. If you later obtain MLS access, the ingest layer can be swapped.

## Project structure
- `src/ingest/`: data source connectors and ingestion runner
- `src/underwrite/`: comps, scoring, and vision hooks
- `src/alerts/`: alert dispatch (email)
- `src/db/`: sqlite schema + helpers
- `config/`: thresholds and env examples
- `docs/`: architecture notes
