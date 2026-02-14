from typing import Dict, Any


def enrich_with_estated(config, conn) -> Dict[str, Any]:
    if not config.estated_api_key:
        return {"status": "skipped", "reason": "missing ESTATED_API_KEY"}

    raise NotImplementedError(
        "Estated enrichment is not wired yet. Add API integration in src/ingest/estated.py."
    )
